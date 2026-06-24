import os
from datetime import datetime, timezone
from tqdm import tqdm
import authenticate
from IO_Functions import Download, Upload
import json
THRESHOLD = 10  # seconds


def get_drive_files(drive, folder_id):
    """Returns a dict of {filename: file_object} for a Drive folder."""
    query = f"'{folder_id}' in parents and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    return {f['title']: f for f in file_list}


def get_drive_mtime(file):
    return datetime.fromisoformat(
        file['modifiedDate'].replace('Z', '+00:00')
    ).timestamp()


def sync(drive, local_path, folder_id,prefix=None):
    os.makedirs(local_path, exist_ok=True)

    drive_files = get_drive_files(drive, folder_id)
    local_files = set(os.listdir(local_path))

    if prefix:
        drive_files = {k: v for k, v in drive_files.items() if k.startswith(prefix)}
        local_files = {f for f in local_files if f.startswith(prefix)}
    all_names = set(drive_files.keys()) | local_files

    for name in all_names:
        local_file_path = os.path.join(local_path, name)
        in_drive = name in drive_files
        in_local = name in local_files

        # --- Only on Drive: download ---
        if in_drive and not in_local:
            drive_file = drive_files[name]
            if drive_file['mimeType'] == 'application/vnd.google-apps.folder':
                tqdm.write(f"[NEW DIR] {name}/ — only on Drive, recursing...")
                sync(drive, local_file_path, drive_file['id'])
            else:
                tqdm.write(f"[NEW] {name} — only on Drive, downloading...")
                drive_file.GetContentFile(local_file_path)
                drive_time = get_drive_mtime(drive_file)
                os.utime(local_file_path, (drive_time, drive_time))

        # --- Only local: upload ---
        elif in_local and not in_drive:
            tqdm.write(f"[NEW] {name} — only local, uploading...")
            new_id = Upload(drive, name, folder_id, local_file_path)
            if os.path.isdir(local_file_path) and new_id:
                tqdm.write(f"[NEW DIR] {name}/ — only local, recursing...")
                sync(drive, local_file_path, new_id)

        # --- Exists in both: compare mtimes ---
        else:
            drive_file = drive_files[name]

            # Recurse into folders without mtime comparison
            if drive_file['mimeType'] == 'application/vnd.google-apps.folder':
                tqdm.write(f"[DIR] {name}/")
                sync(drive, local_file_path, drive_file['id'])
                continue

            drive_time = get_drive_mtime(drive_file)
            local_time = os.path.getmtime(local_file_path)
            diff = drive_time - local_time

            if diff > THRESHOLD:
                tqdm.write(f"[DOWNLOAD] {name} — Drive is newer by {diff:.0f}s")
                Download(drive, name, folder_id, local_file_path)

            elif diff < -THRESHOLD:
                tqdm.write(f"[UPLOAD] {name} — Local is newer by {abs(diff):.0f}s")
                Upload(drive, name, folder_id, local_file_path)

            else:
                tqdm.write(f"[SKIP] {name} — in sync")


if __name__ == '__main__':
    with open("config.json",'r') as file:
        config = json.load(file)
    drive = authenticate.Authenticate()
    folder_id = authenticate.TARGET_FOLDER_ID
    local_path = config['local_path']
    if config['Prefix']=="None":
        prefix=None
    else:
        prefix = config['Prefix']
    sync(drive, local_path, folder_id,prefix)