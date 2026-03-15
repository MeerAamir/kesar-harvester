# Kesar Harvester — Business System

Welcome to the automated business system for Kesar Harvester. This repository contains the direct-to-consumer website and the Python automation suite designed specifically for zero-cost, high-efficiency farming operations.

## 📁 Repository Structure

```
kesar-harvester/
├── web/
│   └── index.html               # Main frontend landing page (Zero dependencies)
├── automation/
│   ├── order_bot.py             # Automates WhatsApp order confirmations & tracking
│   ├── content_gen.py           # Anthropic CLI for IG/YT/B2B content generation
│   ├── lead_tracker.py          # Tracks B2B leads and sends AI-drafted WA reminders
│   ├── requirements.txt         # Python dependencies
│   └── .env.example             # Example environment file
├── content/                     # Auto-generated content is saved here
├── logs/                        # Logs for the bots
└── .github/
    └── workflows/
        └── order_bot.yml        # Configures GitHub Actions 5-min cron
```

## 🛠️ Prerequisites

Before you start, you will need:
- Python 3.10+
- A Google Cloud account (for Sheets API)
- A Twilio account (for WhatsApp Sandbox/API)
- An Anthropic account (for Claude API)

## 🚀 Setup Guides

### 1. Google Sheets API (Database setup)
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project and enable the **Google Sheets API** and **Google Drive API**.
3. Create a **Service Account**, generate a JSON key, and download it.
4. Rename the downloaded file to `credentials.json` and place it in the `automation/` folder.
5. In Google Drive, create a spreadsheet. Make two sheets: `KH_Orders` and `KH_Leads`.
6. **Important:** Share the spreadsheet with the `client_email` found inside your `credentials.json` file (give it Editor access).
7. Copy the Sheet ID from the URL (the long string between `/d/` and `/edit`) and put it in `.env`.

### 2. Twilio WhatsApp Sandbox
1. Create an account at [Twilio](https://www.twilio.com/).
2. Navigate to Messaging > Try it out > Send a WhatsApp message.
3. Accept the Terms and activate the Sandbox.
4. You will get a Twilio Sandbox number (`TWILIO_WA_FROM`).
5. Copy your Account SID and Auth Token to `.env`.
6. *To receive messages in Sandbox mode, you must first send the join code (e.g. "join smooth-bear") to the Twilio number from your personal WhatsApp.*

### 3. Anthropic API
1. Create an account at [Anthropic Console](https://console.anthropic.com/).
2. Generate an API Key.
3. Add it to `.env` as `ANTHROPIC_API_KEY`.

### 4. Deploying the Website
1. Push this repository to GitHub.
2. Go to Repository Settings > Pages.
3. Under "Build and deployment", select **Deploy from a branch**.
4. Choose `main` branch and `/web` folder (or root if you move `index.html`).
5. Wait 2 minutes. Your site is live! Add your custom domain in the settings if needed.

### 5. Running the Cron Bot via GitHub Actions
To let the `order_bot.py` run 24/7 for free:
1. Go to your GitHub Repository > Settings > Secrets and variables > Actions.
2. Add the following **Repository Secrets**:
   - `TWILIO_SID`: Your SID
   - `TWILIO_TOKEN`: Your Token
   - `TWILIO_WA_FROM`: Your WA From number
   - `SHEET_ID`: Your Google Sheet ID
   - `GOOGLE_CREDS`: Open `credentials.json`, copy all text, base64 encode it (`base64 credentials.json` on Mac/Linux), and paste the result here.
3. The `.github/workflows/order_bot.yml` file is already configured to run every 5 minutes.

## 📖 Daily Usage Guide

### Local Setup
```bash
cd automation
pip install -r requirements.txt
cp .env.example .env
```
*(Edit .env with your real keys)*

### Content Generation
Need captions or YouTube descriptions?
```bash
python content_gen.py --topic "Harvesting Mongra Saffron" --product saffron
```
Output is printed to the terminal and saved to the `/content/` folder.

### B2B Follow-Ups
Run this every morning:
```bash
python lead_tracker.py
```
It reads `KH_Leads`, checks who needs a follow-up today, generates a custom message, and sends an alert to your WhatsApp.

### Order Processing
(Handled automatically by GitHub Actions, but you can test it locally)
```bash
python order_bot.py --dry-run
```
