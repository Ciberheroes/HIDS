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
            bytes = f.read()
            hash = hashlib.sha256(bytes).hexdigest()
            metadata = {"uri": archivo, "file_hash": hash}
            # Envía la solicitud POST con el archivo y los datos de metadatos
            response = requests.post(url=f"{server_url}/load", files={"file": bytes}, data=metadata)

# file_list_json = json.dumps(file_list_with_hash)
# for file in file_list_json:
#     print(file_list_json)
#     response = requests.post(url = f"{server_url}/load", data=file_list_json, files=)
#     print(response)

# response = requests.get(url = f"{server_url}/check", data = file_list_json)
# for i in range(4):
#     for file in file_list_json:
#         response = requests.get(server = f"{server_url}/check", data = file)
#         print(response.json())
#     time.sleep(1)
