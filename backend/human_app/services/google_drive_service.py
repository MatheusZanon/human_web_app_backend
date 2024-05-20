import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request


def Create_Service(secret_service_file, api_name, api_version, *scopes):
    #print(f"Secret Service File: {secret_service_file}, API Name: {api_name}, API Version: {api_version}, Scopes: {scopes}")
    SCOPES = [scope for scope in scopes[0]]
    credentials = service_account.Credentials.from_service_account_file(
        secret_service_file, scopes=SCOPES)

    try:
        service = build(api_name, api_version, credentials=credentials)
        print(f'{api_name} service created successfully')
        return service
    except Exception as e:
        print('Unable to connect.')
        print(e)
        return None