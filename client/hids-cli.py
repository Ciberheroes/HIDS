import requests
import os
import hashlib
from datetime import date
import argparse
import json
import schedule
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
server_url = os.getenv("SERVER_URL")
folder_path = os.getenv("FOLDER_PATH")
# Booleano que indica si se deben eliminar los archivos no rastreados
untracked_action = os.getenv("DELETE_UNTRACKED",False) == "True"

def upload_directory():

    for ruta_directorio, carpetas, archivos in os.walk(os.path.join(os.path.dirname(__file__), folder_path)):
        for archivo in archivos:
            with open(os.path.join(ruta_directorio, archivo), "rb") as f:
                file_data = f.read()
                hash = hashlib.sha256(file_data).hexdigest()
                metadata = {"uri": os.path.relpath(os.path.join(ruta_directorio, archivo),os.path.dirname(__file__)), "file_hash": hash, "file": file_data}
                f.seek(0)
                response = requests.post(url=f"{server_url}/load", files={'file': f}, data=metadata)
                if response.status_code == 200:
                    print(f"OK: {archivo} uploaded successfully.")
                else:
                    print(f"ERROR: {archivo}. Server responded with: {response.content}")

def dropload_directory():
    response = requests.get(server_url+ '/drop')
    if response.status_code == 200:
        print("-> Files deleted successfully.\n")
        upload_directory()
    else:
        print(f"ERROR: Failed to delete files. Server responded with: {response.content}")

def restore(uri):
    print(f"-> Restoring file {uri}")
    response = requests.get(server_url +'/restore', params={'uri': uri})
    if response.status_code == 200:
        with open(uri, 'wb') as f:
            f.write(response.content)
        print("OK: File restored successfully.")
    else:
        print(f"ERROR: Failed to restore file. Server responded with: {response.content}")

def check_files():
    file_list_with_hash = []
    for ruta_directorio, _, archivos in os.walk(os.path.join(os.path.dirname(__file__), folder_path)):
        for archivo in archivos:
            with open(os.path.join(ruta_directorio, archivo), "rb") as f:
                file_data = f.read()
                hash = hashlib.sha256(file_data).hexdigest()
                file_list_with_hash.append({"uri": os.path.relpath(os.path.join(ruta_directorio, archivo),os.path.dirname(__file__)), "file_hash": hash})
    response = requests.post(url=f"{server_url}/check", json=json.dumps(file_list_with_hash))
    json_response = response.json()

    untracked = json_response["untracked"]
    modified= json_response["modified"]
    not_found = json_response["not_found"]

    if len(untracked) > 0:
        print("### Untracked files ###\n")
        for file in untracked:
            if untracked_action:
                print(f"-> Deleting file {file['uri']}")
                os.remove(file["uri"])
            else:
                print(file["uri"])
    else:
        print("### No untracked files ###\n")

    if len(modified) > 0:
        print("### Modified files ###\n")
        for file in modified:
            restore(file["uri"])
    else:
        print("### No modified files ###\n")
    
    if len(not_found) > 0:
        print("### Not found files ###\n")
        for file in not_found:
            restore(file["uri"])
    else:
        print("### No deleted files ###\n")

def send_report(day_of_report,month=None,year=None):
    
    if date.today().day == day_of_report:
        print("### Triggering send of report ###\n")
        if month and year:
            response = requests.get(url=f"{server_url}/report", params={'month': month, 'year': year})
        else:
            response = requests.get(url=f"{server_url}/report")
        
        if response.status_code == 200:
            print("OK: Report sent successfully, check your email.")
        else:
            print(f"ERROR: Failed to send report. Server responded with: {response.content}")

def check_periodically(hour_period, day_of_report = 1):
    while True:
        schedule.every(hour_period).hours.do(check_files)
        schedule.every().day.at("00:00").do(send_report(day_of_report))

## TODO: Configuración sobre qué hacer con los untracked

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='hids-cli')
    parser.add_argument('-dl', '--dropload',action="store_true", help='dueletes the current files and loads the directory recursively')
    parser.add_argument('-l', '--load',action="store_true", help='loads the directory recursively')
    parser.add_argument('-c', '--check',action="store_true", help='checks the directory integrity, if no period is set, it will check once instantly')
    parser.add_argument('-cp','--check-period', metavar="", help='sets the checking period (hours)', type=int)
    parser.add_argument('-rp','--report-period', metavar="", help='sets the report period, (day of the month), default day 1 at 00:00', type=int, choices=range(1,32))
    parser.add_argument('-r','--report', metavar="", help='triggers the server to send the repport of the given month and year format yyyy-mm', type=str)

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()

    if args.dropload:
        print("\n... Dropload started ...\n")
        dropload_directory()
        exit(1)

    elif args.load:
        print("\n... Load started ...\n")
        upload_directory()
        exit(1)

    if args.report:
        print("\n... Triggering send of report ...\n")
        try:
            input_date = datetime.strptime(args.report, "%Y-%m")
            send_report(date.today().day,input_date.month,input_date.year)
        except:
            print("ERROR: Invalid date format, use yyyy-mm")
        exit(1)

    if args.check:
        if args.check_period:
            print("\n... Checking periodicaly ...\n")
            check_periodically(args.check_period, args.report_period if args.report_period else 1)
        else:
            if args.report_period:
                print("\n*** No check period supplied, ignoring argument ***\n")
            print("... Checking files ...\n")
            check_files()
        exit(1)

    if args.check_period and not args.check:
        print("\n*** No check argument supplied, ignoring argument ***\n")
        exit(1)
    
    if args.report_period and not args.check:
        print("\n*** No check argument supplied, ignoring argument ***\n")
        exit(1)
    