import hashlib
import re
from flask import Flask, request, Response, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import shutil

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
db = SQLAlchemy(app)

# Email configuration
CLIENT_EMAIL = os.getenv("CLIENT_EMAIL")
APP_EMAIL = os.getenv("APP_EMAIL")
EMAIL_HOST = os.getenv("EMAIL_HOST")
APP_EMAIL_PASSWORD = os.getenv("APP_EMAIL_PASSWORD")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS")
EMAIL_PORT= os.getenv("EMAIL_PORT")

with app.app_context():
    db.create_all()

class File(db.Model):
    uri = db.Column(db.String, primary_key=True)
    file_hash = db.Column(db.String, nullable=False)
    checked_at = db.Column(db.DateTime, nullable=False, default=datetime.now())

def getFile(file):
    with open(os.path.join(os.path.dirname(__file__),"backup", file.uri), 'rb') as f:
        return {
            "uri": file.uri,
            "file": f.read()
        }

@app.route('/drop', methods=['GET'])
def drop():
    db.drop_all()
    db.create_all()
    if os.path.exists(os.path.join(os.path.dirname(__file__),'backup')):
        shutil.rmtree(os.path.join(os.path.dirname(__file__),'backup'))
    return Response("Database dropped and created", status=200)

@app.route('/load', methods=['POST'])
def load():
    uri = request.form['uri']
    file_hash = request.form['file_hash']
    file = request.files['file']

    if not os.path.exists(os.path.join(os.path.dirname(__file__),'backup')):
        os.makedirs(os.path.join(os.path.dirname(__file__),'backup'))

    db_file = db.session.get(File, uri)
    
    try:
        if db_file:
            db_file.file_hash = file_hash
            db_file.checked_at = datetime.now()
            db.session.commit()
        else:
            if (hashlib.sha256(file.read()).hexdigest() == file_hash):
                db_file = File(uri=uri, file_hash=file_hash)
                db.session.add(db_file)
                db.session.commit()
            else :
                return Response("Hashes are not the same: " + uri, status=400)
    except:
        message = "Error saving file in databse: " + uri
        return Response(message, status=500)
        

    if not os.path.exists(os.path.join(os.path.dirname(__file__),'backup',os.path.dirname(uri))):
        os.makedirs(os.path.join(os.path.dirname(__file__),'backup',os.path.dirname(uri)))
        
    file.save(os.path.join(os.path.dirname(__file__),'backup',uri))

    return Response(response="Saved succesfully", status=200)

@app.route('/check', methods=['POST'])
def check(): 
    files = json.loads(request.json)
    now_date = datetime.now()
    
    untracked = []
    modified = []
    not_found = []
        
    try:
        if not os.path.exists(os.path.join(os.path.dirname(__file__),'logs')):
            os.mkdir(os.path.join(os.path.dirname(__file__),'logs'))
    except:
        message = "Error creating logs directory"
        return Response(message, status=500)

    log = open(os.path.join(os.path.dirname(__file__),'logs',now_date.strftime("%Y-%m-%d_%H-%M-%S") + ".log"), "w")
    log.write("********************************************************************\n")
    log.write("Starting a check at " + now_date.strftime("%Y-%m-%d %H:%M:%S") + "\n")
    log.write("********************************************************************\n\n")

    for file in files:
        db_file = db.session.get(File,file['uri'])
        if not db_file:
            untracked.append({"uri": file['uri'], "hash": file['file_hash']})
        else:
            db_file.checked_at = datetime.now()
            if db_file.file_hash != file['file_hash']:    
                modified.append({"uri": file['uri'], "hash": file['file_hash']})

    db.session.commit()
    
    not_found = [{"uri": f.uri,"hash":f.file_hash} for f in File.query.filter(File.checked_at < now_date)]

    if len(untracked) == 0 and  len(modified) == 0 and len(not_found) == 0:
        log.write("No changes found\n")
    else:
        for file in untracked:
            log.write("Untracked file: " + file['uri'] + "\n")
        
        for file in modified:
            log.write("Modified file: " + file['uri'] + "\n")

        for file in not_found:
            log.write("Not found file: " + file['uri'] + "\n")

    return Response(json.dumps({"untracked": untracked,"modified": modified,"not_found": not_found}), status=200, mimetype="application/json")
            
@app.route('/restore', methods=['GET'])
def restore():
    uri = request.args.get('uri')
    file = File.query.get(uri)
    if file:
        try:
            return send_file(os.path.join(os.path.dirname(__file__),'backup',file.uri), as_attachment=True)
        except:
            return Response("Error sending file, file might have been deleted.", status=500)
    else:
        return Response("File not found in server", status=404)

@app.route('/report', methods=['GET']) 
def send_email():
    month = request.args.get('month')
    year = request.args.get('year')
    if month is None:
        month = datetime.now().strftime("%m")
    if year is None:
        year = datetime.now().strftime("%Y")

    email_body = ""

    files = []
    for ruta_directorio, _, archivos in os.walk(os.path.join(os.path.dirname(__file__), 'logs')):
        for archivo in archivos:
            files.append(os.path.join(ruta_directorio, archivo))
    
    files = list(filter(lambda f: re.match(f".*\/{year}-{month.zfill(2)}.*",f),files))
    print(files)
    
    if not files:
        return Response("No logs found", status=404)
    else:
        files = sorted(files, key=lambda f: os.path.getmtime(f))
        for file in files:
            print("Mira este fichero:",file)
            with open(file, 'r') as f:
                email_body += f.read()
                email_body += "\n\n"
    
    print(email_body)
    try:
        message = MIMEMultipart()
        message['From'] = APP_EMAIL
        message['To'] = CLIENT_EMAIL
        message['Subject'] = "HIDS Report: " + year+ "-" + month.zfill(2) 
        message.attach(MIMEText(email_body, 'plain'))
        

        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(APP_EMAIL, APP_EMAIL_PASSWORD)
        server.sendmail(APP_EMAIL, CLIENT_EMAIL, message.as_string())
        server.quit()
        return Response("Report sent successfully, check your email.", status=200)
    except:
        print("Error sending email")
        return Response("Error sending report", status=500)
if __name__ == '__main__':
    
    app.run(debug=True, host='localhost', port=5000)


    