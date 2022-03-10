from __future__ import print_function
import io

import os.path
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
import concurrent.futures
import zipfile

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']

done_files = set()
try:
    with open('done.txt', 'r+') as file:
        for line in file:
            done_files.add(line.rstrip())
except:
    pass

ig_folders = set()
try:
    with open('folders.txt', 'r+') as file:
        for line in file:
            ig_folders.add(line.rstrip())
except:
    pass

executor = concurrent.futures.ProcessPoolExecutor(10)

def main(argv): 

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)
        folder_id = argv[0]
        # Call the Drive v3 API
        return crawller(service, folder_id)

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')

def crawller(service, folder_id, path=''):
    results = service.files().list(
            q= f"'{folder_id}' in parents" , pageSize=1000, fields="nextPageToken, files(id, name, mimeType)").execute()

    while True: 
    
        items = results.get('files', [])
        nextPageToken = results.get('nextPageToken')

        if not items:
            print('No files found.')
            return 

        folders = list(filter(lambda item: item['mimeType'] == 'application/vnd.google-apps.folder' and item['name'] not in ig_folders, items))
        for folder in folders:
            new_path = path + folder['name'] + "/"
            crawller(service, folder['id'], new_path)
        
        files = list(filter(lambda item: item['mimeType'] != 'application/vnd.google-apps.folder' and (path + item['name']) not in done_files, items))
        
        futures = [executor.submit(save_file, service, path, item) for item in files]
        concurrent.futures.wait(futures)
        results = [future.result() for future in futures]

        for result in results:
            if result['status'] == 'OK':
                with open('done.txt', 'a+') as file:
                    file.write(result['file'] + '\r')
            else:
                with open('error.txt', 'a+') as file:
                    file.write(result['file'] + '\r')

        
        if nextPageToken is None:
            with open('folders.txt', 'a+') as file:
                file.write(path[:-1] + '\r')
            break   
        results = service.files().list(
            q= f"'{folder_id}' in parents" , pageSize=1000, pageToken=f"{nextPageToken}" ,fields="nextPageToken, files(id, name, mimeType)").execute()

def save_file(service, path, item):
    name = path + item['name']
    try:
        if '/' in name:
            os.makedirs(os.path.dirname(name), exist_ok=True)
        file_id = item['id']
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(name, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %s:  %d%%." % (name,int(status.progress() * 100)))
        if '.zip' in name:
            print(f'Unzinping file: {name}')
            with zipfile.ZipFile(name, 'r') as zip_ref:
                zip_ref.extractall(os.path.splitext(name)[0])
        return {'status':'OK', 'file': name}  
    except:
        return {'status':'FAIL', 'file': name}  
        
if __name__ == '__main__':
    main(sys.argv[1:])
    