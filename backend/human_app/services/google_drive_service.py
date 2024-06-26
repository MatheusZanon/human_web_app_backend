import os
from google.auth import identity_pool, external_account, load_credentials_from_file
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def Create_Service():
    # Path to the JSON file with the federation configuration
    current_directory = os.path.dirname(__file__)
    
    # Path to the JSON file with the federation configuration
    federation_config_file = os.path.join(current_directory, 'federation_config.json')
    try:
        # Load the external account credentials
        credentials, project = load_credentials_from_file(federation_config_file)

        # Define the scopes required for accessing Google Drive API
        SCOPES = ['https://www.googleapis.com/auth/drive']
        
         # Ensure credentials have the required scopes
        credentials = credentials.with_scopes(SCOPES)
        
        # Refresh the credentials to obtain a valid token
        credentials.refresh(Request())
        
        # Build the service object for the Google Drive API
        service = build('drive', 'v3', credentials=credentials)
        
        return service

    except Exception as e:
        print(f"An error occurred: {e}")