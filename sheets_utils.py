# sheets_utils.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

load_dotenv()

# Service Account Scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "summary1")

def sheets_auth():
    """Authenticate with Google Sheets API using service account"""
    if not os.path.exists('service-account.json'):
        raise FileNotFoundError(
            "service-account.json file not found. Please download it from Google Cloud Console:\n"
            "1. Go to https://console.cloud.google.com/\n"
            "2. IAM & Admin → Service Accounts\n"
            "3. Create or select your service account\n"
            "4. Create key (JSON) and save as 'service-account.json'"
        )
    
    try:
        # Load service account credentials
        credentials = service_account.Credentials.from_service_account_file(
            'service-account.json', 
            scopes=SCOPES
        )
        
        # Build service without cache_discovery parameter
        return build('sheets', 'v4', credentials=credentials).spreadsheets()
        
    except Exception as e:
        logging.error(f"Service account authentication failed: {e}")
        raise Exception(
            f"Service account authentication failed: {e}\n\n"
            "Please check:\n"
            "1. service-account.json file is valid\n"
            "2. Service account has access to Google Sheets API\n"
            "3. Spreadsheet is shared with service account email"
        )

def get_sheets_service():
    """Get authenticated Sheets service"""
    return sheets_auth()

def append_to_sheet(service, senders: str, subjects: str, emails: str, summary: str):
    """Append combined email data to spreadsheet"""
    try:
        if not SPREADSHEET_ID:
            raise ValueError("SPREADSHEET_ID not set in environment variables")
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # First check if headers exist
        try:
            result = service.values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A1:E1"
            ).execute()
            
            if not result.get('values'):
                # Add headers if sheet is empty
                service.values().append(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"{SHEET_NAME}!A1",
                    valueInputOption="RAW",
                    body={"values": [["Timestamp", "Sender", "Subject", "Email", "Summary"]]}
                ).execute()
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError("Insufficient permissions to access the spreadsheet")
            raise

        # Append the data
        service.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:E",
            valueInputOption="RAW",
            body={
                "values": [[
                    timestamp,
                    senders,
                    subjects,
                    emails,
                    summary
                ]]
            }
        ).execute()
        
        # logging.info(f"Added batch of {len(senders.split('\n'))} emails to spreadsheet")
        
    except Exception as e:
        logging.error(f'Error appending to sheet: {e}')
        raise


def test_sheets_connection():
    """Test Google Sheets connection"""
    try:
        if not SPREADSHEET_ID:
            print("❌ SPREADSHEET_ID not found in .env file")
            return False
        
        print("🔍 Testing service account authentication...")
        service = sheets_auth()
        
        # Test reading from spreadsheet
        result = service.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1:E1"
        ).execute()
        
        print(f"✅ Sheets connection successful!")
        print(f"   Spreadsheet ID: {SPREADSHEET_ID}")
        print(f"   Sheet name: {SHEET_NAME}")
        print(f"   Authentication: Service Account")
        
        values = result.get('values', [])
        if values:
            print(f"   Headers: {values[0]}")
        else:
            print("   Sheet is empty (will add headers automatically)")
        
        return True
        
    except Exception as e:
        print(f"❌ Sheets connection failed: {e}")
        return False

if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_sheets_connection()

