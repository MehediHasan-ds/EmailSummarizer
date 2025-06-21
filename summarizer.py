from groq import Groq
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        
def summarize_email(text: str) -> str:
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system", 
                    "content": "You are processing multiple emails at once. Each email starts with 'Sender: [sender]', 'Subject: [subject]', and 'Body: [content]'. "
                    "Provide a comprehensive summary that covers all emails, highlighting: "
                    "1. Key senders and their main points "
                    "2. Common themes across emails "
                    "3. Important action items "
                    "4. Any urgent matters "
                    "Format your response with clear sections and bullet points."
                },
                {
                    "role": "user", 
                    "content": text
                }
            ],
            temperature=0.3,  # Lower for more consistent summaries
            max_tokens=500,   # Increased for longer summaries
            top_p=0.9
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating summary: {str(e)}"
    
