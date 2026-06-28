# Email Statement Service

Upload edited bank statement PDFs and send them via email with AES-256 password protection.

**Flow:** Upload edited PDF → Encrypt with password (last 4 digits of account) → Send via email → Recipient opens with password.

## Features

- **📤 Upload PDF** — Upload your pre-edited bank statement PDF for any account
- **🔐 AES-256 Encryption** — PDFs are encrypted with password = last 4 digits of account number
- **📧 Email Sending** — Configure SMTP and send encrypted PDFs to any email address
- **📊 Access Tracking** — See when and from where PDFs are accessed
- **🔗 BGV Verification** — Generate bank portal pages and verification links for background verification
- **📨 Auto-Responder** — Automatically reply to BGV verification emails from your company inbox

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
| GET | `/api/replace?accountId=X` | Serve the uploaded PDF (encrypted) |
| GET | `/api/list` | List all uploaded PDFs |
| POST | `/api/email/config` | Save SMTP configuration |
| GET | `/api/email/config` | Get SMTP configuration status |
| POST | `/api/email/send` | Send encrypted PDF via email |
| GET | `/api/access-log` | View PDF access logs |
| GET | `/api/health` | Health check |

## How It Works

1. **Edit your statement** using any PDF editor (Adobe Acrobat, browser print-to-PDF, etc.)
2. **Upload** the edited PDF to this service for a specific account number
3. **Configure SMTP** (Gmail, Outlook, etc.) in the Email tab
4. **Send** the encrypted PDF to any email address
5. **Recipient opens** the PDF with password = last 4 digits of account number

## Tech Stack

- **Backend:** Python + FastAPI + SQLAlchemy
- **PDF Encryption:** PyMuPDF (AES-256)
- **Database:** PostgreSQL (Docker) / SQLite (dev)
- **Email:** SMTP via smtplib
