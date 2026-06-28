# Email Statement Service

Upload edited bank statement PDFs and send them via email with AES-256 password protection — the email appears to come from the bank's official statement delivery system.

**Flow:** Upload edited PDF → Encrypt with password (last 4 digits of account) → Send via email → Recipient opens with password

## Features

- **📤 Upload & Send** — Upload your pre-edited bank statement PDF and send it directly to any email in one step
- **🏦 Bank-Like Emails** — Emails appear as if they came from the bank, with bank branding
- **🔐 AES-256 Encryption** — PDFs are encrypted with password = last 4 digits of account number (same as real banks)
- **🏛️ All Banks Supported** — Any bank name works; email dynamically shows the bank name as sender
- **📧 Email Sending** — Configure SMTP (Gmail, Outlook, etc.) once, then send to anyone
- **📊 Access Tracking** — See when and from where PDFs are accessed
- **🔗 BGV Verification** — Generate bank portal pages and verification links for background verification
- **📨 Auto-Responder** — Automatically reply to BGV verification emails from your company inbox
- **🔌 Chrome Extension** — Intercept real bank PDF downloads and replace with your edited statement

## Quick Start

### Using Docker

```bash
docker-compose up --build
```

Open http://localhost:8080 in your browser.

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL (or use SQLite for development)
# Edit app/config.py to set DATABASE_URL

# Run the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Open http://localhost:8080 in your browser.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload an edited PDF for an account |
| POST | `/api/upload-and-send` | Upload PDF and send directly via email in one call |
| GET | `/api/replace?accountId=X` | Serve the uploaded PDF (encrypted) |
| GET | `/api/list` | List all uploaded PDFs |
| POST | `/api/email/config` | Save SMTP configuration |
| GET | `/api/email/config` | Get SMTP configuration status |
| POST | `/api/email/send` | Send encrypted PDF via email |
| GET | `/api/access-log` | View PDF access logs |
| GET | `/api/health` | Health check |

## How It Works

1. **Edit your statement** using any PDF editor (Adobe Acrobat, browser print-to-PDF, etc.)
2. **Upload & send** — Enter the account number, upload your edited PDF, enter the recipient's email and bank name. The system encrypts the PDF and sends it via email in one step.
3. **Email looks bank-sent** — The email appears to come from the bank's statement delivery system with proper bank branding.
4. **Recipient opens** the PDF with password = last 4 digits of account number — just like a real bank statement.

**First-time setup:** Configure SMTP (Gmail, Outlook, etc.) in the Email & Tracking tab.

## Tech Stack

- **Backend:** Python + FastAPI + SQLAlchemy
- **PDF Encryption:** PyMuPDF (AES-256)
- **Database:** PostgreSQL (Docker) / SQLite (dev)
- **Email:** SMTP via smtplib
