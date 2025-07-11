# utils.py

import json
import io
import re
import unicodedata
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
APP_FOLDER_NAME = "PatentAppData"

# ✅ Secure filename generator
def secure_filename(value: str, allow_uuid_suffix: bool = False) -> str:
    import uuid
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w.\- ]", "", value)
    value = re.sub(r"\s+", "_", value).strip("._")
    if not value:
        value = "file"
    if allow_uuid_suffix:
        value += f"_{uuid.uuid4().hex[:6]}"
    return value

@st.cache_resource(show_spinner="🔐 Authenticating with Google Drive...")
def authenticate():
    secrets = st.secrets["gcp_oauth"]

    creds = Credentials(
        token=secrets.get("access_token"),
        refresh_token=secrets["refresh_token"],
        token_uri=secrets["token_uri"],
        client_id=secrets["client_id"],
        client_secret=secrets["client_secret"],
        scopes=SCOPES
    )

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            st.error(f"Failed to refresh Google credentials: {e}")
            st.stop()

    return build('drive', 'v3', credentials=creds)

def get_or_create_folder(service):
    results = service.files().list(
        q=f"name='{APP_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        spaces='drive',
        fields="files(id, name)"
    ).execute()
    items = results.get('files', [])
    if items:
        return items[0]['id']
    file_metadata = {'name': APP_FOLDER_NAME, 'mimeType': 'application/vnd.google-apps.folder'}
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder['id']

def upload_json_to_drive(filename, data):
    filename = secure_filename(filename)
    if not isinstance(data, dict) or not data:
        st.error("❌ Cannot upload empty or invalid JSON data.")
        return

    service = authenticate()
    folder_id = get_or_create_folder(service)
    json_str = json.dumps(data, indent=4, ensure_ascii=False)
    bytes_io = io.BytesIO(json_str.encode('utf-8'))

    results = service.files().list(
        q=f"name='Summary_{filename}.json' and '{folder_id}' in parents and trashed=false",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    items = results.get('files', [])

    if items:
        file_id = items[0]['id']
        service.files().update(
            fileId=file_id,
            media_body=MediaIoBaseUpload(bytes_io, mimetype='application/json', resumable=True)
        ).execute()
    else:
        metadata = {'name': f"Summary_{filename}.json", 'parents': [folder_id]}
        service.files().create(
            body=metadata,
            media_body=MediaIoBaseUpload(bytes_io, mimetype='application/json', resumable=True),
            fields='id'
        ).execute()

def download_json_from_drive(filename):
    filename = secure_filename(filename)
    service = authenticate()
    folder_id = get_or_create_folder(service)
    results = service.files().list(
        q=f"name='Summary_{filename}.json' and '{folder_id}' in parents and trashed=false",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    items = results.get('files', [])
    if not items:
        return {}

    file_id = items[0]['id']
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    return json.load(fh)

# Final aliases for app.py
def backup_to_drive(filename, data):
    upload_json_to_drive(filename, data)

def load_from_drive(filename):
    return download_json_from_drive(filename)
