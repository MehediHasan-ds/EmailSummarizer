# Intelligent Email Summarizer Agent

An intelligent email processing system that automatically fetches unread emails from Gmail, generates AI-powered summaries using LLAMA via Groq, and stores the results in Google Sheets with a beautiful Streamlit dashboard for monitoring.

## Features

- **Automated Email Processing**: Batch processes all unread emails
- **AI-Powered Summaries**: Uses LLAMA 3 via Groq API for intelligent summarization  
- **Google Sheets Integration**: Automatically saves summaries to spreadsheet
- **Real-time Dashboard**: Streamlit web interface for monitoring and manual triggers
- **FastAPI Backend**: RESTful API with background scheduling
- **Smart Email Handling**: Marks emails as read after processing to avoid duplicates
- **Hybrid Authentication**: OAuth 2.0 for Gmail + Service Account for Sheets

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Gmail API     │    │   FastAPI        │    │  Google Sheets  │
│   (OAuth 2.0)   │◄──►│   Backend        │◄──►│ (Service Acc.)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Groq/LLAMA     │
                       │   Summarizer     │
                       └──────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Streamlit      │
                       │   Dashboard      │
                       └──────────────────┘
```

## Project Structure

```
email-summarizer/
├── main.py                 # FastAPI application with scheduler
├── gmail_utils.py          # Gmail API utilities
├── sheets_utils.py         # Google Sheets API utilities  
├── summarizer.py           # Groq/LLAMA integration
├── auth_setup.py           # Authentication setup wizard
├── dashboard.py            # Streamlit dashboard
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── credentials.json        # Gmail OAuth credentials (download from Google Cloud)
├── service-account.json    # Sheets service account (download from Google Cloud)
├── token.json              # Generated Gmail token (auto-created)
└── README.md              # This file
```

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Google Cloud Project with APIs enabled
- Groq API account

### 2. Clone and Install

```bash
git clone https://github.com/MehediHasan-ds/EmailSummarizer.git
cd email-summarizer
pip install -r requirements.txt
```

### 3. Environment Setup

Create `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
SPREADSHEET_ID=your_google_sheets_id
SHEET_NAME=summary1
BACKEND_URL=http://localhost:8000
```

### 4. Google Cloud Setup

#### Gmail API (OAuth 2.0)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select project → APIs & Services → Library
3. Enable **Gmail API**
4. Go to Credentials → Create OAuth 2.0 Client ID
5. Application type: **Desktop Application**
6. Add redirect URI: `http://localhost:8080/`
7. Download as `credentials.json`

#### Google Sheets API (Service Account)  
1. Go to IAM & Admin → Service Accounts
2. Create service account: `emailsummarizer-sheets`
3. Create JSON key → Download as `service-account.json`
4. **Important**: Share your Google Sheet with the service account email

### 5. Authentication Setup

Run the setup wizard:
```bash
python auth_setup.py
```

This will:
-  Authenticate Gmail OAuth
-  Validate service account  
-  Test API connections
-  Create test spreadsheet

### 6. Run the System

Start the backend:
```bash
uvicorn main:app --reload
```

Start the dashboard (new terminal):
```bash
streamlit run frontend.py
```

## Detailed Setup Guide

### Google Cloud Project Setup

1. **Create Project**
   ```
   Project Name: EmailSummarizer
   Project ID: email-summarizer-[random-id]
   ```

2. **Enable APIs**
   - Gmail API
   - Google Sheets API

3. **OAuth Consent Screen**
   - User Type: External (for personal Gmail)
   - Add your Gmail to test users

### Groq API Setup

1. Visit [Groq Console](https://console.groq.com/)
2. Create account → Generate API key
3. Add to `.env` file

### Google Sheets Preparation

1. Create new Google Sheet
2. Add headers: `Timestamp | Sender | Subject | Email | Summary`
3. Copy Sheet ID from URL
4. Share with service account email (from `service-account.json`)

## Configuration

### Email Processing Settings

In `main.py`, adjust the scheduler interval:
```python
scheduler.add_job(
    func=auto_summarize_job,
    trigger=IntervalTrigger(minutes=1),  # Change frequency here
    # ...
)
```

### Summary Customization

In `summarizer.py`, modify the system prompt:
```python
"content": "You are processing multiple emails... [customize instructions]"
```

### Spreadsheet Format

The system saves data in this format:
- **Timestamp**: When processed
- **Sender**: All senders (newline separated)  
- **Subject**: All subjects (newline separated)
- **Email**: All email bodies (double newline separated)
- **Summary**: Combined AI summary

## Dashboard Features

### System Status
-  Backend connection health
-  Gmail API status  
-  Sheets API status

### Manual Controls
-  **Check New Emails**: Process unread emails immediately
-  **Refresh Data**: Reload dashboard data

### Analytics
-  Email activity timeline
-  Sender distribution  
-  Detailed email summaries

## Security & Privacy

### Authentication Methods
- **Gmail**: OAuth 2.0 (user consent required)
- **Sheets**: Service Account (no user interaction)

### Data Privacy
- Emails processed locally
- Summaries stored in your Google Sheet
- API keys stored in local `.env` file
- No data sent to external services (except Groq for summarization)

### Token Management
- Gmail tokens auto-refresh
- Service account credentials don't expire
- All credentials stored locally

## Troubleshooting

### Common Issues

#### "Gmail API access denied"
```bash
python auth_setup.py
```

#### "Service account has no access"
- Ensure Google Sheet is shared with service account email
- Check service account email in `service-account.json`

#### "Groq API rate limit"
- Check API quota in Groq console
- Reduce processing frequency in scheduler

#### "Backend connection failed"
- Ensure FastAPI is running: `uvicorn main:app --reload`
- Check port 8000 is available
- Verify `BACKEND_URL` in `.env`

### Debug Mode

Enable detailed logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Testing Individual Components

Test Gmail connection:
```bash
python -c "from gmail_utils import gmail_auth; gmail_auth()"
```

Test Sheets connection:
```bash
python sheets_utils.py
```

Test summarizer:
```bash
python -c "from summarizer import summarize_email; print(summarize_email('Test email'))"
```

## System Monitoring

### Health Check Endpoint
```bash
curl http://localhost:8000/health
```

### Manual Processing
```bash
curl http://localhost:8000/process-unread-emails
```

### Logs
- Backend: Console output from `uvicorn main:app --reload`
- Dashboard: Console output from `streamlit run dashboard.py`
- Gmail API: Check Google Cloud Console logs

## Workflow

1. **Email Arrival**: New emails arrive in Gmail
2. **Scheduler Check**: Background job runs every minute
3. **Fetch Unread**: System gets all unread emails
4. **AI Processing**: LLAMA generates combined summary
5. **Sheet Update**: Data saved to Google Sheets
6. **Mark Read**: Emails marked as read in Gmail
7. **Dashboard**: Real-time updates in web interface

## Production Deployment

### Environment Variables
```env
GROQ_API_KEY=prod_key_here
SPREADSHEET_ID=prod_sheet_id
DISABLE_SCHEDULER=false
BACKEND_URL=https://your-domain.com
```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

### Scaling Considerations
- Increase Groq API limits
- Use Redis for caching
- Implement email batching
- Add database storage

## License

This project is licensed under the MIT License.

## Acknowledgments

- **Groq**: AI inference platform
- **Google APIs**: Gmail and Sheets integration
- **FastAPI**: Modern web framework
- **Streamlit**: Beautiful dashboards
- **LLAMA**: Large language model

## Useful Links

- [Groq Documentation](https://console.groq.com/docs)
- [Gmail API Guide](https://developers.google.com/gmail/api)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)

---
