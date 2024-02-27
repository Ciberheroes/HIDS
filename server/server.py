from flask import Flask, request, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
from werkzeug.serving import WSGIRequestHandler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)


# File model
class File(db.Model):
    uri = db.Column(db.String, primary_key=True)
    file_hash = db.Column(db.String, nullable=False)
    checked_at = db.Column(db.DateTime, nullable=False, default=datetime.now())

with app.app_context():
    db.drop_all()
    db.create_all()

def getFile(file):
    with open(os.path.join(os.path.dirname(__file__),"backup", file.uri), 'rb') as f:
        return {
            "uri": file.uri,
            "file": f.read()
        }

@app.route('/load', methods=['POST'])
def load():
    uri = request.form['uri']
    file_hash = request.form['file_hash']
    file = request.files['file']

    db_file = db.session.get(File, uri)
    
    try:
        if db_file:
            db_file.file_hash = file_hash
            db_file.checked_at = datetime.now()
            db.session.commit()
        else:
            db_file = File(uri=uri, file_hash=file_hash)
            print(db_file)
            db.session.add(db_file)
            db.session.commit()
    except:
        message = "Error saving file in databse: " + uri
        return Response(message, status=500)
        

    if not os.path.exists(os.path.join(os.path.dirname(__file__),'backup',os.path.dirname(uri))):
        os.makedirs(os.path.join(os.path.dirname(__file__),'backup',os.path.dirname(uri)))
        

    ##Se puede reemplazar el archivo???
    file.save(os.path.join(os.path.dirname(__file__),'backup',uri))

    return Response(response="Saved succesfully", status=200)

@app.route('/check', methods=['POST'])
def check(): 
    files = json.loads(request.json)
    now_date = datetime.now()
    
    log = open(os.path.join(os.path.dirname(__file__),'logs',now_date.strftime("%Y-%m-%d-%H-%M-%S") + ".log"), "w")
    
    untracked = []
    modified = []
    not_found = []
        
    try:
        if not os.path.exists(os.path.join(os.path.dirname(__file__),'logs')):
            os.mkdir(os.path.join(os.path.dirname(__file__),'logs'))
    except:
        message = "Error creating logs directory"
        return Response(message, status=500)

    for file in files:
        db_file = db.session.get(File,file['uri'])
        print(File.query.all())
        if not db_file:
            untracked.append({"uri": file['uri'], "hash": file['file_hash']})
        else:
            db_file.checked_at = datetime.now()
            if db_file.file_hash != file['file_hash']:    
                modified.append({"uri": file['uri'], "hash": file['file_hash']})

    db.session.commit()
    
    not_found = [getFile(f) for f in File.query.filter(File.checked_at < now_date)]
    
    return Response(json.dumps({"untracked": untracked,"modified": modified,"not_found": not_found}), status=200, mimetype="application/json")
            
    

excluded_directories = [os.path.join(os.path.dirname(__file__),'backup'), os.path.join(os.path.dirname(__file__),'logs')]
     
if __name__ == '__main__':
    #app.run(debug=True, host='localhost', port=5000, use_reloader=False)
    app.run(debug=True, host='localhost', port=5000)


    