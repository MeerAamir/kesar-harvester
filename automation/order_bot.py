import os
import sys
import argparse
import logging
import gspread
from dotenv import load_dotenv
from twilio.rest import Client
from google.oauth2.service_account import Credentials

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "bot.log")),
        logging.StreamHandler()
    ]
)

# Load env variables
load_dotenv()

# Constants
SHEET_ID = os.getenv("SHEET_ID")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_WA_FROM = os.getenv("TWILIO_WA_FROM")
GOOGLE_CREDS_PATH = os.getenv("GOOGLE_CREDS_PATH")

def get_sheet_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    if not GOOGLE_CREDS_PATH or not os.path.exists(GOOGLE_CREDS_PATH):
        logging.error(f"Google credentials not found at {GOOGLE_CREDS_PATH}")
        sys.exit(1)
    
    creds = Credentials.from_service_account_file(GOOGLE_CREDS_PATH, scopes=scopes)
    client = gspread.authorize(creds)
    return client

def send_whatsapp(to_number, message, dry_run=False):
    # Ensure number has international code format
    if not to_number.startswith('+'):
        to_number = f"+{to_number}"
    
    if dry_run:
        logging.info(f"[DRY-RUN] Would send WA to {to_number}: {message[:50]}...")
        return True
        
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        msg = client.messages.create(
            from_=f"whatsapp:{TWILIO_WA_FROM}",
            body=message,
            to=f"whatsapp:{to_number}"
        )
        logging.info(f"Sent WA to {to_number}, SID: {msg.sid}")
        return True
    except Exception as e:
        logging.error(f"Failed to send WA to {to_number}: {e}")
        return False

def process_orders(dry_run=False):
    logging.info(f"Starting order processing... {'(DRY RUN)' if dry_run else ''}")
    
    try:
        gc = get_sheet_client()
        sheet = gc.open_by_key(SHEET_ID).worksheet("KH_Orders")
    except Exception as e:
        logging.error(f"Failed to connect to Google Sheets KH_Orders: {e}")
        return

    records = sheet.get_all_records()
    if not records:
        logging.info("No records found in KH_Orders.")
        return

    # Assuming headers: timestamp, name, city, phone, product, size, status, wa_sent, dispatched, tracking_sent
    headers = sheet.row_values(1)
    
    for idx, row in enumerate(records):
        row_num = idx + 2 # Since header is row 1
        
        status = str(row.get('status', '')).strip().lower()
        wa_sent = str(row.get('wa_sent', '')).strip().lower()
        tracking_sent = str(row.get('tracking_sent', '')).strip().lower()
        
        name = row.get('name', 'Customer')
        product = row.get('product', '')
        size = row.get('size', '')
        phone = str(row.get('phone', '')).strip()
        
        if not phone:
            continue
            
        # 1. Confirmed -> Send Order Confirmation
        if status == "confirmed" and wa_sent == "no":
            msg = f"Hello {name}! 🌾\n\nYour order for {product} ({size}) from Kesar Harvester has been CONFIRMED.\n\nWe are preparing it straight from our farm. You'll receive a tracking number once dispatched."
            
            if send_whatsapp(phone, msg, dry_run):
                if not dry_run:
                    col_index = headers.index('wa_sent') + 1
                    sheet.update_cell(row_num, col_index, 'yes')
                    logging.info(f"Updated row {row_num} wa_sent='yes'")
        
        # 2. Dispatched -> Send Tracking Details
        elif status == "dispatched" and tracking_sent == "no":
            msg = f"Great news {name}! 🚚\n\nYour Kesar Harvester order ({product}) has been DISPATCHED.\n\nIt should reach you in 3-5 days via Speed Post. Thank you for choosing farm-direct purity!"
            
            if send_whatsapp(phone, msg, dry_run):
                if not dry_run:
                    col_index = headers.index('tracking_sent') + 1
                    sheet.update_cell(row_num, col_index, 'yes')
                    logging.info(f"Updated row {row_num} tracking_sent='yes'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kesar Harvester Order Bot")
    parser.add_argument("--dry-run", action="store_true", help="Print messages instead of sending and do not update sheets")
    args = parser.parse_args()
    
    process_orders(dry_run=args.dry_run)
