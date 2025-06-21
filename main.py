from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from gmail_utils import gmail_auth, fetch_latest_email, fetch_unread_emails, mark_as_read
from summarizer import summarize_email
from sheets_utils import sheets_auth, append_to_sheet
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from contextlib import asynccontextmanager
import logging
import uvicorn
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler
scheduler = BackgroundScheduler()

def auto_summarize_job():
    """Background job to check and summarize emails"""
    try:
        gmail_service = gmail_auth()
        sheet_service = sheets_auth()

        # Fetch all unread emails
        unread_emails = fetch_unread_emails(gmail_service)
        if not unread_emails:
            logger.info("No unread emails found")
            return

        msg_ids = []
        senders = []
        subjects = []
        bodies = []
        
        # Process each email
        for msg_id, sender, subject, body in unread_emails:
            msg_ids.append(msg_id)
            senders.append(sender)
            subjects.append(subject)
            bodies.append(body)

        # Combine all emails into one text for summarization
        combined_text = "\n\n".join(
            f"Sender: {sender}\nSubject: {subject}\nBody: {body}"
            for sender, subject, body in zip(senders, subjects, bodies)
        )

        # Generate single summary for all emails
        summary = summarize_email(combined_text)
        
        # Prepare data for spreadsheet
        combined_senders = "\n".join(senders)
        combined_subjects = "\n".join(subjects)
        combined_bodies = "\n\n".join(bodies)
        
        # Append to sheet
        append_to_sheet(
            sheet_service,
            combined_senders,
            combined_subjects,
            combined_bodies,
            summary
        )
        
        # Mark emails as read after successful processing
        mark_as_read(gmail_service, msg_ids)
        
        logger.info(f"Processed {len(unread_emails)} emails")

    except Exception as e:
        logger.error(f"Error in auto_summarize_job: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not os.getenv("DISABLE_SCHEDULER", "").lower() == "true":
        scheduler.add_job(
            func=auto_summarize_job,
            trigger=IntervalTrigger(minutes=1),
            id='email_summarizer_job',
            name='Auto Email Summarizer',
            replace_existing=True
        )
        scheduler.start()
        logger.info("Email summarizer scheduler started")
    else:
        logger.info("Scheduler disabled via environment variable")
    
    yield
    
    # Shutdown
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Email summarizer scheduler stopped")

app = FastAPI(
    title="Email Summarizer API",
    description="Automatically summarize emails and save to Google Sheets",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": f"Internal server error: {str(exc)}"},
    )

@app.get("/")
async def root():
    return {
        "message": "Email Summarizer API is running",
        "endpoints": {
            "/summarize-latest": "GET - Manually fetch and summarize latest email",
            "/process-unread-emails": "GET - Process all unread emails in batch",
            "/health": "GET - Service health check"
        }
    }

@app.get("/process-unread-emails")
async def process_unread_emails():
    """Process all unread emails in batch"""
    try:
        gmail_service = gmail_auth()
        sheet_service = sheets_auth()

        unread_emails = fetch_unread_emails(gmail_service)
        if not unread_emails:
            return {"message": "No unread emails found", "count": 0}

        msg_ids = []
        senders = []
        subjects = []
        bodies = []
        
        for msg_id, sender, subject, body in unread_emails:
            msg_ids.append(msg_id)
            senders.append(sender)
            subjects.append(subject)
            bodies.append(body)

        combined_text = "\n\n".join(
            f"Sender: {sender}\nSubject: {subject}\nBody: {body}"
            for sender, subject, body in zip(senders, subjects, bodies)
        )

        summary = summarize_email(combined_text)
        
        append_to_sheet(
            sheet_service,
            "\n".join(senders),
            "\n".join(subjects),
            "\n\n".join(bodies),
            summary
        )
        
        mark_as_read(gmail_service, msg_ids)
        
        return {
            "status": "success",
            "count": len(unread_emails),
            "senders": senders,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/summarize-latest")
async def summarize_and_store():
    """Manually trigger email summarization"""
    try:
        gmail_service = gmail_auth()
        sheet_service = sheets_auth()

        sender, subject, email = fetch_latest_email(gmail_service)
        if not sender:
            return {"message": "No unread email found."}
        
        summary = summarize_email(f"Sender: {sender}\nSubject: {subject}\nBody: {email}")
        append_to_sheet(sheet_service, sender, subject, email, summary)
        
        return {
            "status": "success",
            "sender": sender,
            "subject": subject,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in manual summarization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        gmail_service = gmail_auth()
        gmail_status = "connected" if gmail_service else "disconnected"
    except:
        gmail_status = "disconnected"
    
    try:
        sheet_service = sheets_auth()
        sheets_status = "connected" if sheet_service else "disconnected"
    except:
        sheets_status = "disconnected"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "gmail": gmail_status,
            "sheets": sheets_status
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

