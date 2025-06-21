# auth_setup.py
"""
Complete authentication setup for Gmail + Sheets integration
Gmail: OAuth 2.0 (credentials.json → token.json)
Sheets: Service Account (service-account.json)
"""

import os
import logging
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Gmail OAuth Scopes
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Sheets Service Account Scopes
SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def clean_existing_auth():
    """Remove existing token to force re-authentication"""
    if os.path.exists('token.json'):
        try:
            os.remove('token.json')
            print("✅ Removed existing token.json")
        except Exception as e:
            print(f"⚠️  Could not remove token.json: {e}")

def authenticate_gmail():
    """Authenticate Gmail with OAuth 2.0"""
    
    # Check for credentials file
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json file not found!")
        print("\nPlease follow these steps for Gmail OAuth:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Select your project (or create one)")
        print("3. Go to APIs & Services → Library")
        print("4. Enable 'Gmail API'")
        print("5. Go to APIs & Services → Credentials")
        print("6. Create OAuth 2.0 Client ID (Desktop application)")
        print("7. Download as 'credentials.json' in this directory")
        print("8. Make sure OAuth redirect URIs include: http://localhost:8080/")
        return None
    
    try:
        # Create OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', GMAIL_SCOPES)
        
        # Run local server for authentication
        creds = flow.run_local_server(
            port=8080,
            host='localhost',
            open_browser=True,
            success_message='✅ Gmail authentication successful! You can close this window.'
        )
        
        # Save credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        
        print("✅ Successfully authenticated Gmail with OAuth!")
        print("✅ Gmail credentials saved to token.json")
        
        return creds
        
    except Exception as e:
        print(f"❌ Gmail authentication failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check that your credentials.json is valid")
        print("2. Ensure OAuth redirect URIs include: http://localhost:8080/")
        print("3. Verify Gmail API is enabled")
        print("4. Check OAuth consent screen configuration")
        return None

def check_service_account():
    """Check service account setup for Sheets"""
    
    if not os.path.exists('service-account.json'):
        print("❌ service-account.json file not found!")
        print("\nPlease follow these steps for Sheets Service Account:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Go to IAM & Admin → Service Accounts")
        print("3. Create Service Account: 'emailsummarizer-sheets'")
        print("4. Create JSON key and download as 'service-account.json'")
        print("5. Note the service account email (ends with .iam.gserviceaccount.com)")
        print("6. Share your Google Sheet with this service account email")
        return None
    
    try:
        # Load and validate service account
        credentials = service_account.Credentials.from_service_account_file(
            'service-account.json', 
            scopes=SHEETS_SCOPES
        )
        
        # Get service account email
        with open('service-account.json', 'r') as f:
            import json
            sa_data = json.load(f)
            sa_email = sa_data.get('client_email', 'Unknown')
        
        print("✅ Service account file found and valid!")
        print(f"✅ Service account email: {sa_email}")
        print("📝 Make sure your spreadsheet is shared with this email!")
        
        return credentials
        
    except Exception as e:
        print(f"❌ Service account validation failed: {e}")
        return None

def test_gmail_access(creds):
    """Test Gmail API access"""
    try:
        service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
        
        # Test getting user profile
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress', 'Unknown')
        
        print(f"✅ Gmail API access successful!")
        print(f"   Connected to: {email_address}")
        
        # Test getting recent emails
        result = service.users().messages().list(
            userId='me', 
            maxResults=1
        ).execute()
        
        message_count = len(result.get('messages', []))
        print(f"   Can access emails: {message_count} messages found")
        
        return True
        
    except HttpError as e:
        print(f"❌ Gmail API test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Gmail API test error: {e}")
        return False

def test_sheets_access(creds):
    """Test Google Sheets API access with service account"""
    try:
        service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
        
        # Try to create a test spreadsheet
        spreadsheet = {
            'properties': {
                'title': 'Email Summarizer Test Sheet (Service Account)'
            }
        }
        
        result = service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = result['spreadsheetId']
        
        print(f"✅ Sheets API access successful!")
        print(f"   Created test spreadsheet: {spreadsheet_id}")
        
        # Add some test headers
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A:E',
            valueInputOption='RAW',
            body={'values': [['Timestamp', 'Sender', 'Subject', 'Email', 'Summary']]}
        ).execute()
        
        print(f"   Test data added successfully")
        print(f"   📝 You can use this spreadsheet ID: {spreadsheet_id}")
        print(f"   🔗 View at: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        
        return True, spreadsheet_id
        
    except HttpError as e:
        print(f"❌ Sheets API test failed: {e}")
        return False, None
    except Exception as e:
        print(f"❌ Sheets API test error: {e}")
        return False, None

def main():
    """Main authentication setup process"""
    print("🚀 Email Summarizer Hybrid Authentication Setup")
    print("=" * 60)
    print("Gmail: OAuth 2.0 | Sheets: Service Account")
    print("=" * 60)
    
    # Step 1: Clean existing authentication
    print("\n📋 Step 1: Cleaning existing Gmail authentication...")
    clean_existing_auth()
    
    # Step 2: Authenticate Gmail with OAuth
    print("\n📋 Step 2: Authenticating Gmail with OAuth 2.0...")
    gmail_creds = authenticate_gmail()
    
    # Step 3: Check Service Account setup
    print("\n📋 Step 3: Checking Sheets Service Account setup...")
    sheets_creds = check_service_account()
    
    if not gmail_creds:
        print("\n❌ Gmail authentication failed. Please check the instructions above.")
        return
    
    if not sheets_creds:
        print("\n❌ Service account setup incomplete. Please check the instructions above.")
        return
    
    # Step 4: Test Gmail access
    print("\n📋 Step 4: Testing Gmail API access...")
    gmail_success = test_gmail_access(gmail_creds)
    
    # Step 5: Test Sheets access
    print("\n📋 Step 5: Testing Sheets API access...")
    sheets_success, test_spreadsheet_id = test_sheets_access(sheets_creds)
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 HYBRID SETUP SUMMARY")
    print("=" * 60)
    
    if gmail_success and sheets_success:
        print("✅ Hybrid authentication successful!")
        print("✅ Gmail API access: Working (OAuth 2.0)")
        print("✅ Sheets API access: Working (Service Account)")
        print(f"✅ Test spreadsheet created: {test_spreadsheet_id}")
        print("\n📝 Next steps:")
        print("1. Update your .env file with:")
        print("   - GROQ_API_KEY=your_groq_key")
        print("   - SPREADSHEET_ID=your_actual_spreadsheet_id")
        print("   - SHEET_NAME=summary1")
        print("2. Share your actual spreadsheet with the service account email")
        print("3. Run your email summarizer: python main.py")
        print("4. Or test with: python sheets_utils.py")
    else:
        print("❌ Setup incomplete:")
        if not gmail_success:
            print("   - Gmail API access failed")
        if not sheets_success:
            print("   - Sheets API access failed")
        print("\nPlease check the error messages above and try again.")

if __name__ == "__main__":
    main()


