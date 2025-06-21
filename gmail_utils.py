# gmail_utils.py
import base64
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Tuple, Optional, List
import logging

# COMBINED SCOPES - This is the key fix!
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',  # Changed from readonly to modify
    'https://www.googleapis.com/auth/spreadsheets'
]

def gmail_auth():
    """Authenticate with Gmail API using combined scopes"""
    creds = None
    
    # Load existing token
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception as e:
            logging.warning(f"Error loading existing token: {e}")
            # Delete corrupted token file
            if os.path.exists('token.json'):
                os.remove('token.json')
            creds = None
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logging.info("Successfully refreshed token")
            except Exception as e:
                logging.error(f"Error refreshing token: {e}")
                # Delete the invalid token and re-authenticate
                if os.path.exists('token.json'):
                    os.remove('token.json')
                creds = None
        
        if not creds:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "credentials.json file not found. Please download it from Google Cloud Console:\n"
                    "1. Go to https://console.cloud.google.com/\n"
                    "2. APIs & Services → Credentials\n"
                    "3. Download OAuth 2.0 Client ID as 'credentials.json'"
                )
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                
                # Use a specific port that matches your OAuth configuration
                creds = flow.run_local_server(
                    port=8080,
                    host='localhost',
                    open_browser=True,
                    success_message='Authentication successful! You can close this window.'
                )
                
                logging.info("Successfully obtained new credentials with combined scopes")
                
            except Exception as e:
                logging.error(f"OAuth flow failed: {e}")
                raise Exception(
                    f"OAuth authentication failed: {e}\n\n"
                    "Please check:\n"
                    "1. Your credentials.json file is valid\n"
                    "2. OAuth redirect URIs include: http://localhost:8080/\n"
                    "3. Gmail API and Sheets API are enabled in Google Cloud Console\n"
                    "4. Your OAuth consent screen is configured"
                )
        
        # Save credentials for next run
        try:
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            logging.info("Credentials saved to token.json")
        except Exception as e:
            logging.warning(f"Could not save token: {e}")
    
    return build('gmail', 'v1', credentials=creds)

def get_credentials():
    """Get authenticated credentials for use in other modules"""
    creds = None
    
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception as e:
            logging.warning(f"Error loading token: {e}")
            return None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logging.error(f"Error refreshing credentials: {e}")
                return None
        else:
            return None
    
    return creds

def fetch_latest_email(service) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Fetch the latest unread email"""
    try:
        # Get unread emails
        result = service.users().messages().list(
            userId='me', 
            maxResults=1, 
            q="is:unread"
        ).execute()
        
        if not result.get('messages'):
            logging.info("No unread emails found")
            return None, None, None
        
        msg_id = result['messages'][0]['id']
        msg = service.users().messages().get(
            userId='me', 
            id=msg_id, 
            format='full'
        ).execute()
        
        # Extract headers
        headers = msg['payload'].get('headers', [])
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        
        # Extract body
        body = extract_body(msg['payload'])
        
        # Mark as read (optional)
        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        
        logging.info(f"Successfully fetched email from {sender} with subject: {subject}")
        return sender, subject, body
        
    except HttpError as error:
        logging.error(f'Gmail API error: {error}')
        return None, None, None
    except Exception as e:
        logging.error(f'Unexpected error fetching email: {e}')
        return None, None, None

def extract_body(payload) -> str:
    """Extract email body from payload"""
    body = ""
    
    def get_body_recursive(part):
        nonlocal body
        if part.get('mimeType') == 'text/plain':
            data = part.get('body', {}).get('data')
            if data:
                try:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    return True
                except Exception as e:
                    logging.warning(f"Error decoding plain text body: {e}")
        elif part.get('mimeType') == 'text/html' and not body:
            data = part.get('body', {}).get('data')
            if data:
                try:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                except Exception as e:
                    logging.warning(f"Error decoding HTML body: {e}")
        
        # Check parts recursively
        if 'parts' in part:
            for subpart in part['parts']:
                if get_body_recursive(subpart):
                    return True
        return False
    
    get_body_recursive(payload)
    
    # Clean up and limit body
    if body:
        body = ' '.join(body.split())
        body = body[:2000]
    
    return body or "No readable content found"


def fetch_unread_emails(service, max_results=10) -> List[Tuple[str, str, str, str]]:
    """Fetch all unread emails and return list of (msg_id, sender, subject, body)"""
    try:
        # Get unread emails
        result = service.users().messages().list(
            userId='me', 
            maxResults=max_results, 
            q="is:unread"
        ).execute()
        
        if not result.get('messages'):
            logging.info("No unread emails found")
            return []
        
        emails = []
        for msg in result['messages']:
            msg_id = msg['id']
            msg_data = service.users().messages().get(
                userId='me', 
                id=msg_id, 
                format='full'
            ).execute()
            
            # Extract headers
            headers = msg_data['payload'].get('headers', [])
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            
            # Extract body
            body = extract_body(msg_data['payload'])
            
            emails.append((msg_id, sender, subject, body))
        
        return emails
        
    except HttpError as error:
        logging.error(f'Gmail API error: {error}')
        return []
    except Exception as e:
        logging.error(f'Unexpected error fetching emails: {e}')
        return []

def mark_as_read(service, msg_ids):
    """Mark messages as read"""
    if not msg_ids:
        return
        
    try:
        for msg_id in msg_ids:
            service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        logging.info(f"Marked {len(msg_ids)} emails as read")
    except Exception as e:
        logging.error(f"Error marking emails as read: {e}")

def count_unread_emails(service):
    """Count number of unread emails"""
    try:
        result = service.users().messages().list(
            userId='me',
            q="is:unread"
        ).execute()
        return result.get('resultSizeEstimate', 0)
    except Exception as e:
        logging.error(f"Error counting unread emails: {e}")
        return 0