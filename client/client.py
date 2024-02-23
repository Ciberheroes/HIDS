import requests
import time
import json
import os
import hashlib

server_url = "http://localhost:5000"
folder_path = "file_system"

file_list_with_hash = []

for ruta_directorio, carpetas, archivos in os.walk(os.path.join(os.path.dirname(__file__), folder_path)):
    for archivo in archivos:
        with open(os.path.join(ruta_directorio, archivo), "rb") as f:
            file_data = f.read()
            hash = hashlib.sha256(file_data).hexdigest()
            metadata = {"uri": os.path.relpath(os.path.join(ruta_directorio, archivo),os.path.dirname(__file__)), "file_hash": hash, "file": file_data}
            # Mueve el puntero del archivo al principio
            f.seek(0)
            # Envía la solicitud POST con el archivo y los datos de metadatos
            response = requests.post(url=f"{server_url}/load", files={'file': f}, data=metadata)
