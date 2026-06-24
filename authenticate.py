from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os as os
from datetime import datetime,timezone
import json as json
import threading as threading
from tqdm import *

auth_lock = threading.Lock()
with open("config.json",'r') as file:
    config = json.load(file)


TARGET_FOLDER_ID = config['TARGET_FOLDER_ID']

def Authenticate():
    tqdm.write("Authenticating with Drive")
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("MyCreds.txt")

    if gauth.credentials is None:
        tqdm.write("No saved credentials found... Opening Browser...")
        gauth.GetFlow()
        gauth.flow.scope = 'https://www.googleapis.com/auth/drive'
        gauth.flow.params.update({'access_type':'offline'})
        gauth.flow.params.update({'approval_prompt':'force'})
        gauth.LocalWebserverAuth()

    elif gauth.access_token_expired:
        tqdm.write("Credentials expired. Refreshing...")
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile("MyCreds.txt")
    return GoogleDrive(gauth)
