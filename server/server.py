from flask import Flask, request, make_response, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
import sys

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)


# File model
class File(db.Model):
    uri = db.Column(db.String, primary_key=True)
    file_hash = db.Column(db.String, nullable=False)
    checked_at = db.Column(db.DateTime, nullable=False, default=datetime.now())

def getFile(file):
    with open(os.path.join(os.curdir,"backup", file.uri), 'rb') as f:
        return {
            "uri": file.uri,
            "file": f.read()
        }

@app.route('/load', methods=['POST'])
def load():
    # data = json.loads(request.get_data("data"))
    uri = request.form['uri']
    file_hash = request.form['file_hash']
    file_bytes = request.form['file']
    new_file = None
    try:
        new_file = File(uri=uri, file_hash=file_hash)
    except:
        message = "Error parsing file: " + uri
        return Response(message, status=500)
    
    # try:
    #     if not os.path.exists('backup'):
    #         os.mkdir('backup')
    #     if not os.path.exists('backup/'+uri):
    #         fd = os.open('backup/'+uri, os.O_WRONLY | os.O_CREAT)
    #         os.close(fd)
    #     with open('backup/'+uri, 'wb') as file:
    #         file.write(bytes(file_bytes))

    # except Exception as e:
    #     message = "Error saving the file: " + uri
    #     return Response(e, status=500)

    if not os.path.exists('backup'):
        os.mkdir('backup')
    if not os.path.exists('backup/'+uri):
        fd = os.open('backup/'+uri, os.O_WRONLY | os.O_CREAT)
        os.close(fd)
    with open('backup/'+uri, 'wb') as file:
        file.write(bytes(file_bytes))

    db.session.add(new_file)
    db.session.commit()

    return Response(response="Saved succesfully", status=200)

@app.route('/check', methods=['POST'])
def check():
    files = request.get_json()
    now_date = datetime.now()
    new_files = []
        
    for file in files:
        file = File.query.get(file['uri'])
        if not file:
            ##Se pueden añadir archivos nuevos???
            new_files.append(File(uri=file['uri'], file_hash=file['hash'], date=now_date))
        else:
            File.query.filter_by(uri=file['uri']).update(date=datetime.now())

    db.session.commit()
    not_found = [getFile(f) for f in File.query.filter(lambda x: x.checked_at < now_date)]
    
    return Response(json.dumps(new_files,not_found), status=200, mimetype="application/json")
            
    
if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)


    