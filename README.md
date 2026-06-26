# Bank Statement Replacer

Replaces real bank statement PDF downloads with custom encrypted PDFs using a Spring Boot backend + Chrome Extension.

## Architecture

```
User clicks PDF link on bank website
         │
         ▼
Chrome Extension intercepts request (declarativeNetRequest)
         │
         ▼
Redirects to → http://localhost:8080/api/statements/replace?accountId=XXXXX
         │
         ▼
Spring Boot looks up custom PDF for accountId
         │
         ▼
Encrypts PDF with AES-256 (password = last 4 digits of accountId)
         │
         ▼
Returns encrypted PDF → prompts for password when opened
```

## Prerequisites

- Java 17+
- Maven 3.8+
- Chrome browser

## Project Structure

```
email-statement/
├── backend/                          # Spring Boot 3.2 app
│   ├── pom.xml
│   └── src/main/
│       ├── java/com/bankstatement/
│       │   ├── BankStatementApplication.java
│       │   ├── config/WebConfig.java
│       │   ├── controller/StatementController.java
│       │   ├── entity/Statement.java
│       │   ├── repository/StatementRepository.java
│       │   └── service/PdfEncryptionService.java
│       └── resources/
│           ├── application.properties
│           └── data.sql
├── extension/                        # Chrome Extension (MV3)
│   ├── manifest.json
│   ├── background.js
│   ├── popup.html
│   └── popup.js
├── generate-test-pdf.ps1             # Generate a sample test PDF
└── upload-test-pdf.bat               # Upload helper (Windows)
```

## Step 1: Build & Run the Backend

```bash
cd backend
mvn clean package -DskipTests
java -jar target/bank-statement-1.0.0.jar
```

Or use Maven directly:
```bash
cd backend
mvn spring-boot:run
```

The API will be available at `http://localhost:8080`.

## Step 2: Load the Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right)
3. Click **Load unpacked**
4. Select the `extension/` folder
5. The extension "Bank Statement Replacer" will appear

## Step 3: Upload Your Custom PDF

### Option A: Using the batch script (Windows)
```bash
# First generate a test PDF
powershell -ExecutionPolicy Bypass -File generate-test-pdf.ps1

# Then upload it
upload-test-pdf.bat test-statement.pdf
```

### Option B: Using curl directly
```bash
# Generate and upload
curl -X POST http://localhost:8080/api/statements/upload \
  -F "accountId=1234567890" \
  -F "file=@test-statement.pdf"
```

Replace `1234567890` with your actual bank account number.
Replace the file path with your own custom PDF.

### Option C: Upload via API with your real statement
```bash
curl -X POST http://localhost:8080/api/statements/upload \
  -F "accountId=YOUR_ACCOUNT_ID" \
  -F "file=@/path/to/your/custom-statement.pdf"
```

## Step 4: Configure the Extension

1. Click the extension icon in Chrome toolbar
2. Enter your **Bank Domain URL** (e.g., `https://onlinebanking.yourbank.com`)
3. Enter your **Account ID** (must match what you used in Step 3)
4. Click **Save Settings**

The extension will automatically set up a redirect rule to intercept PDFs from your bank.

## Step 5: Test the Flow

### Quick test without the extension:
Open this URL in your browser:
```
http://localhost:8080/api/statements/replace?accountId=1234567890
```
Your browser will download an encrypted PDF. Open it - it should ask for a password.

### Full flow test:
1. Make sure the backend is running
2. Make sure the extension is loaded and configured
3. Navigate to any PDF URL on your bank's domain (or simulate by visiting `https://your-bank-domain.com/test.pdf`)
4. The extension will redirect to your local API
5. You'll receive the encrypted custom PDF

## PDF Password

The PDF encryption password is the **last 4 digits of your account ID**.

Example:
- Account ID: `1234567890`
- Password: `7890`

The Owner password (for removing restrictions) is: `bank_owner_key`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/statements/replace?accountId=XXX` | Get encrypted replacement PDF |
| POST | `/api/statements/upload` | Upload a custom PDF for an account |
| GET | `/api/statements/list` | List all uploaded statements |
| GET | `/h2-console` | H2 database console (dev only) |

## Troubleshooting

- **Extension not intercepting**: Make sure the bank domain in extension settings matches exactly. Check `chrome://extensions/` -> Service Worker console for logs.
- **PDF not opening**: Make sure you have a PDF reader that supports AES-256 encryption (Adobe Reader, Chrome built-in PDF viewer).
- **Backend not starting**: Ensure Java 17+ and Maven 3.8+ are installed and on your PATH.
- **CORS errors**: The backend already allows all origins. If you see issues, check that the backend is running on port 8080.

## Customization

To change the encryption password logic, edit `StatementController.java`:
```java
// Change this line to use a different password scheme
String password = accountId.substring(Math.max(0, accountId.length() - 4));
```

To change the owner password, edit `PdfEncryptionService.java`:
```java
stamper.setEncryption(
    userPassword.getBytes(),
    "bank_owner_key".getBytes(),  // ← change this
    ...
);
```
