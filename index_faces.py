import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import re

# --- CONFIGURATION ---
# 1. UPDATE THIS: The name of your Google Sheet
#    (as it appears in your Google Drive)
SHEET_NAME = "get_your_photos" 

# 2. This is the file with your "robot" password
CREDENTIALS_FILE = 'credentials.json' 

# 3. This is the folder where we'll save the downloaded photos
DOWNLOAD_FOLDER = 'reference_photos'
# ---------------------

# Define the "scopes" or permissions our script needs
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Helper function to get the File ID from a Google Drive URL
def get_google_drive_file_id(url):
    """Extracts the file ID from a Google Drive URL."""
    # This regular expression matches the file ID in various GDrive URL formats
    match = re.search(r'file/d/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    return None

def main():
    # --- 1. AUTHENTICATE ---
    print("Authenticating...")
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    
    # Authenticate for Google Sheets
    gc = gspread.authorize(creds)
    
    # Authenticate for Google Drive
    drive_service = build('drive', 'v3', credentials=creds)
    
    # Create the download folder if it doesn't exist
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

    # --- 2. OPEN THE SHEET & GET DATA ---
    try:
        print(f"Opening Google Sheet: '{SHEET_NAME}'...")
        sheet = gc.open(SHEET_NAME).sheet1
        records = sheet.get_all_records()
        print(f"Found {len(records)} registered users.")
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"ERROR: Spreadsheet not found: '{SHEET_NAME}'.")
        print("Please check the SHEET_NAME variable in your script.")
        return
    except Exception as e:
        print(f"An error occurred opening the sheet: {e}")
        return

    # --- 3. DOWNLOAD PHOTOS ---
    for user in records:
        full_name = user['name']
        email = user['email']
        photo_url = user['upload_your_reference image']
        
        # Clean the name to create a valid filename
        safe_filename = "".join([c for c in full_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        local_photo_path = os.path.join(DOWNLOAD_FOLDER, f"{safe_filename}_{email}.jpg")
        
        # Check if we already downloaded this photo
        if os.path.exists(local_photo_path):
            print(f"Skipping {full_name} (photo already downloaded).")
            continue

        file_id = get_google_drive_file_id(photo_url)
        
        if not file_id:
            print(f"Could not find a valid Google Drive file ID for {full_name}. Skipping.")
            continue

        try:
            # Prepare the request to download the file
            request = drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Downloading photo for {full_name}... {int(status.progress() * 100)}%")
            
            # Save the downloaded file to disk
            with open(local_photo_path, 'wb') as f:
                f.write(fh.getvalue())
            print(f"Saved photo for {full_name} to {local_photo_path}")

        except Exception as e:
            print(f"Error downloading photo for {full_name}: {e}")

    print("\nDownload process complete.")

if __name__ == '__main__':
    main()