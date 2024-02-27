import requests
import os
import hashlib
from datetime import date
import argparse
import json
import schedule

server_url = "http://localhost:5000"
folder_path = "file_system"

def upload_directory():

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

def check_files():
    file_list_with_hash = []
    for ruta_directorio, _, archivos in os.walk(os.path.join(os.path.dirname(__file__), folder_path)):
        for archivo in archivos:
            with open(os.path.join(ruta_directorio, archivo), "rb") as f:
                file_data = f.read()
                hash = hashlib.sha256(file_data).hexdigest()
                file_list_with_hash.append({"uri": os.path.relpath(os.path.join(ruta_directorio, archivo),os.path.dirname(__file__)), "file_hash": hash})
    response = requests.post(url=f"{server_url}/check", json=json.dumps(file_list_with_hash))
    print(response.text)

def send_report(day_of_report, manual = False):
    
    if date.today().day == day_of_report or manual:
        print("### Triggering send of report ###")
        response = requests.post(url=f"{server_url}/report")
        print(response.text)

def check_periodically(hour_period, day_of_report = 1):
    while True:
        schedule.every(hour_period).hours.do(check_files)
        schedule.every().day.at("00:00").do(send_report(day_of_report))



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='hids-cli')
    parser.add_argument('-l', '--load',action="store_true", help='soads the directory recursively')
    parser.add_argument('-c', '--check',action="store_true", help='checks the directory integrity, if no period is set, it will check once instantly')
    parser.add_argument('-cp','--check-period', metavar="", help='sets the checking period (hours), default 24h', type=int, default=86400)
    parser.add_argument('-rp','--report-period', metavar="", help='sets the report period, (day of the month), default day 1 at 00:00', type=int, default=1, choices=range(1,32))
    parser.add_argument('-r','--report', action="store_true", help='triggers the server to send the repport instantly')

    #parse args
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()

    if args.load:
        print("### Load started ####")
        upload_directory()

    elif args.check:
        print("### Checking integrity ###")
        check_files()

    if args.check_period:
        print("### Checking periodically every " + str(args.check_period) + "s")
        check_periodically(args.check_period)
    