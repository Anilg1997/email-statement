# Bank Statement Editor (Python + PostgreSQL)

Python port of the Bank Statement Editor & BGV Verification Portal.
FastAPI + PostgreSQL + ReportLab.

## Quick Start

### Option 1: Docker (Recommended)

```bash
docker-compose up --build
```

Open http://localhost:8080

### Option 2: Local

1. Install PostgreSQL and create a database:
```bash
createdb bank_editor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure `.env`:
```bash
cp .env.example .env
# Edit DATABASE_URL in .env
```

4. Run:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## Features

All features from the Java version:
- Statement Editor with bank-specific PDF templates
- Upload PDF for replacement
- PDF Import with text extraction
- AES-256 encryption (password = last 4 digits of account)
- BGV Verification Portal with bank portal viewer
- Email templates and SMTP sending
- Access tracking
- Chrome Extension support

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/generate | Generate encrypted PDF |
| POST | /api/generate-plain | Generate plain PDF |
| POST | /api/preview | Preview PDF inline |
| POST | /api/upload | Upload PDF for replacement |
| GET | /api/list | List uploaded PDFs |
| GET | /api/replace | Serve replacement PDF |
| POST | /api/import-pdf | Extract data from real PDF |
| POST | /api/bgv/store-statement | Store for BGV |
| POST | /api/bgv/generate-link | Create verification link |
| GET | /api/bgv/view/{id} | Bank portal page |
| POST | /api/bgv/email-template | Email template |
| GET | /api/bgv/links | List verification links |
| POST | /api/email/config | Configure SMTP |
| GET | /api/email/config | Get email config |
| POST | /api/email/send | Send PDF via email |
| GET | /api/access-log | Access tracking logs |

## Database

PostgreSQL with SQLAlchemy async ORM. Schema created automatically on startup.
