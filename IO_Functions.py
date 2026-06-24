from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os as os
from datetime import datetime,timezone
import json as json
import threading as threading
from tqdm import tqdm

#Downloads only when the modified time of gdrive file is ahead
def Download(drive,filename,folder_id,save_path):
    query = f"title='{filename}' and '{folder_id}' in parents and trashed=false"
    File_List = drive.ListFile({'q' :query}).GetList()

    if not File_List:
        tqdm.write(f"[!] Error: Could'nt find '{filename}'")
        return False
    for file in File_List:
        if(file['title']==filename):
            local_time = os.path.getmtime(save_path)
            drive_time = datetime.fromisoformat(file['modifiedDate'].replace('Z','+00:00')).timestamp()

            if abs(drive_time-local_time)>10:
                tqdm.write("The drive file is ahead. Downloading...")
                file.GetContentFile(save_path)
                tqdm.write(">>Download Complete!")
                os.utime(save_path,(drive_time,drive_time))

                return True
#This Doesn't check times      
def Upload(drive,filename,file_id,local_file_path):
    query =  f"title='{filename}' and '{file_id}' in parents and trashed=false"
    File_List = drive.ListFile({'q' :query}).GetList()
    local_timestamp = os.path.getmtime(local_file_path)
    local_date_iso = datetime.fromtimestamp(local_timestamp, tz=timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    if File_List and len(File_List)>0:
        file = File_List[0]
        tqdm.write(f"Found File: {filename} id: {File_List[0]['id']}")
        tqdm.write(f"Uploading new {filename} to drive...")
        gfile = drive.CreateFile({
            'id': file['id'],
            'supportsAllDrives': True,
            'modifiedDate' : local_date_iso
        })
        if(os.path.isdir(local_file_path)):
            tqdm.write("Existing Folder")
            return gfile['id']
        else:
            gfile.SetContentFile(local_file_path)
            gfile.Upload(param={'supportsAllDrives':True,'setModifiedDate':True})
    else:
        tqdm.write(f"First time uploading this file : '{filename}'")
        if(os.path.isdir(local_file_path)):
            gfile = drive.CreateFile({
                'title':filename,
                'parents':[{'id':file_id}],
                'mimeType':'application/vnd.google-apps.folder',
                'modifiedDate':local_date_iso
            })
            gfile.Upload(param={'supportsAllDrives':True,'setModifiedDate':True})
        else:
            gfile = drive.CreateFile({
                'title':filename,
                'parents': [{'id':file_id}],
                'modifiedDate': local_date_iso
            })
            gfile.SetContentFile(local_file_path)
            gfile.Upload(param={'supportsAllDrives':True,'setModifiedDate':True})
            tqdm.write(f">>Upload Complete!")
    return gfile['id']


