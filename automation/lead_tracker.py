import os
import sys
import argparse
import datetime
import logging
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from twilio.rest import Client
from google import genai

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "lead_bot.log")),
        logging.StreamHandler()
    ]
)

# Load env variables
load_dotenv()

SHEET_ID = os.getenv("SHEET_ID")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_WA_FROM = os.getenv("TWILIO_WA_FROM")
GOOGLE_CREDS_PATH = os.getenv("GOOGLE_CREDS_PATH")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Provide owner's phone for self-notifications - could be in .env but using config WA here for simplicity
OWNER_PHONE = "918825034663"

def get_sheet_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    if not GOOGLE_CREDS_PATH or not os.path.exists(GOOGLE_CREDS_PATH):
        logging.error(f"Google credentials not found at {GOOGLE_CREDS_PATH}")
        sys.exit(1)
    
    creds = Credentials.from_service_account_file(GOOGLE_CREDS_PATH, scopes=scopes)
    return gspread.authorize(creds)

def send_whatsapp(to_number, message, dry_run=False):
    if not to_number.startswith('+'):
        to_number = f"+{to_number}"
    
    if dry_run:
        logging.info(f"[DRY-RUN] Would send WA to {to_number}:\n{message}\n")
        return True
        
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        msg = client.messages.create(
            from_=f"whatsapp:{TWILIO_WA_FROM}",
            body=message,
            to=f"whatsapp:{to_number}"
        )
        logging.info(f"Sent WA reminder to owner, SID: {msg.sid}")
        return True
    except Exception as e:
        logging.error(f"Failed to send WA to {to_number}: {e}")
        return False

def generate_followup_message(name, company, product, quantity, notes):
    system_prompt = "You are the owner of Kesar Harvester, a direct-from-farm Kashmiri brand. You grow saffron yourself. You are writing a short, polite B2B WhatsApp follow-up message."
    user_prompt = f"""Write a very brief WhatsApp follow-up message to {name} from {company}.
They previously inquired about: {quantity} of {product}.
Context notes: {notes}

Requirements:
- Under 60 words
- Warm but professional tone (Hinglish/English mix)
- Re-iterate direct farmer pricing
- Ask if they are still interested or need a sample
"""
    try:
        if not GEMINI_API_KEY:
            return "(Gemini API key missing. Please write message manually.)"
            
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
            ),
        )
        return response.text.strip()
    except Exception as e:
        logging.error(f"Failed to generate Gemini message: {e}")
        return "(Failed to generate AI message due to error)"

def check_leads(dry_run=False):
    logging.info(f"Checking B2B Leads for follow-ups... {'(DRY RUN)' if dry_run else ''}")
    
    try:
        gc = get_sheet_client()
        sheet = gc.open_by_key(SHEET_ID).worksheet("KH_Leads")
    except Exception as e:
        logging.error(f"Failed to connect to Google Sheets KH_Leads: {e}")
        return

    records = sheet.get_all_records()
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    leads_to_follow_up = []
    
    for row in records:
        status = str(row.get('status', '')).strip().lower()
        follow_date = str(row.get('followup_date', '')).strip()
        
        if status != "closed" and follow_date == today_str:
            leads_to_follow_up.append(row)
            
    if not leads_to_follow_up:
        logging.info("No leads scheduled for follow-up today.")
        return
        
    logging.info(f"Found {len(leads_to_follow_up)} leads to follow up on today.")
    
    for lead in leads_to_follow_up:
        name = lead.get('name', 'Client')
        company = lead.get('company', 'Company')
        product = lead.get('product', 'product')
        quantity = lead.get('quantity', 'bulk')
        notes = lead.get('notes', 'No notes provided')
        
        logging.info(f"Processing follow-up for {name} ({company})...")
        
        # 1. Generate suggested message
        ai_message = generate_followup_message(name, company, product, quantity, notes)
        
        # 2. Format notification for owner
        notification = f"🚨 *B2B LEAD REMINDER* 🚨\n\n"
        notification += f"*Client:* {name} at {company}\n"
        notification += f"*Interest:* {quantity} of {product}\n"
        notification += f"*Notes:* {notes}\n\n"
        notification += f"*Suggested WA Msg:*\n{ai_message}"
        
        # 3. Send to Owner via Twilio
        send_whatsapp(OWNER_PHONE, notification, dry_run=dry_run)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kesar Harvester Lead Tracker")
    parser.add_argument("--dry-run", action="store_true", help="Print instead of sending WA messages")
    args = parser.parse_args()
    
    check_leads(dry_run=args.dry_run)
