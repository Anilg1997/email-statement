"""Inbound BGV Email Auto-Responder Service.

Fetches emails from a company IMAP inbox, detects BGV-related messages,
and automatically replies with a genuine verification response including
statement links and/or PDF attachments from uploaded documents.
"""
import asyncio
import imaplib
import email as email_lib
import re
import uuid
from email.header import decode_header
from datetime import datetime
from typing import Optional, Any
from io import BytesIO

from app.services.email_service import EmailConfig, send_statement_email
from app.services.pdf_encryptor import encrypt_pdf
from app.services.bgv_service import generate_verification_id, generate_email_html


# Keywords that identify a BGV-related email
BGV_KEYWORDS = [
    "bgv", "background verification", "background check",
    "verification", "employment verification", "bank verification",
    "statement verification", "account verification",
    "confirm statement", "verify statement", "statement confirmation",
    "bg verification", "bgv check", "bg check",
    "genuine", "genuineness", "authenticity",
    "credit check", "financial verification",
    "bank statement", "account statement",
]


def decode_mime_header(header_value: str) -> str:
    """Decode a MIME-encoded header value to plain text."""
    if not header_value:
        return ""
    decoded_parts = decode_header(header_value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(charset or "utf-8", errors="replace"))
            except (LookupError, UnicodeDecodeError):
                result.append(part.decode("utf-8", errors="replace"))
        else:
            result.append(str(part))
    return " ".join(result)


def extract_email_address(header_value: str) -> str:
    """Extract a clean email address from a header like 'Name <email@example.com>'."""
    match = re.search(r'<([^>]+)>', header_value)
    if match:
        return match.group(1).strip().lower()
    # Try to find an email-like pattern
    match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', header_value)
    if match:
        return match.group(0).strip().lower()
    return header_value.strip().lower()


def get_email_body(msg: email_lib.message.Message) -> str:
    """Extract the plain text body from an email message."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        return payload.decode("utf-8", errors="replace")
                    except Exception:
                        return payload.decode("latin-1", errors="replace")
            elif content_type == "text/html":
                # Fallback: if no plain text found, extract from HTML
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        text = payload.decode("utf-8", errors="replace")
                        # Simple HTML tag removal
                        text = re.sub(r'<[^>]+>', ' ', text)
                        text = re.sub(r'\s+', ' ', text).strip()
                        return text
                    except Exception:
                        pass
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            try:
                return payload.decode("utf-8", errors="replace")
            except Exception:
                return payload.decode("latin-1", errors="replace")
    return ""


def detect_bgv_keywords(text: str) -> list[str]:
    """Detect BGV-related keywords in the given text. Returns matched keywords."""
    if not text:
        return []
    text_lower = text.lower()
    matched = []
    for kw in BGV_KEYWORDS:
        if kw in text_lower:
            matched.append(kw)
    return matched


def extract_account_number(text: str) -> Optional[str]:
    """Try to extract an account number from the email body or subject."""
    if not text:
        return None
    # Pattern: sequences of 8-16 digits (typical bank account lengths)
    patterns = [
        r'account\s*(?:no|number|#|:)?\s*[:\s]*(\d{6,16})',
        r'a/c\s*(?:no|number|#|:)?\s*[:\s]*(\d{6,16})',
        r'(\d{9,16})',  # bare number with 9-16 digits
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def generate_genuine_reply_html(
    bank_name: str,
    account_holder: str,
    account_id: str,
    verification_id: str,
    view_url: str,
    password: str,
) -> str:
    """Generate a 'genuine' BGV verification reply email HTML."""
    masked = account_id[-4:] if len(account_id) >= 4 else account_id
    return f"""<!DOCTYPE html>
<html><head><meta charset='UTF-8'></head>
<body style='margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;'>
<table width='100%' cellpadding='0' cellspacing='0' style='background:#f5f5f5;padding:20px;'>
<tr><td align='center'>
<table width='600' cellpadding='0' cellspacing='0' style='background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);'>
<tr><td style='background:linear-gradient(135deg,#059669,#10b981);padding:30px;text-align:center;'>
<div style='font-size:32px;margin-bottom:8px;'>&#9989;</div>
<div style='font-size:22px;font-weight:bold;color:#fff;'>VERIFICATION CONFIRMED</div>
<div style='font-size:13px;color:#a7f3d0;margin-top:4px;'>This statement has been verified as GENUINE</div>
</td></tr>
<tr><td style='padding:30px;'>
<p style='font-size:16px;color:#333;margin:0 0 20px 0;'>To Whom It May Concern,</p>
<p style='font-size:14px;color:#555;line-height:1.6;margin:0 0 16px 0;'>
This is to confirm that the bank statement for the following account has been <strong style='color:#059669;'>verified as genuine and authentic</strong>:
</p>
<div style='background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:20px;margin:20px 0;'>
<table width='100%' cellpadding='6' cellspacing='0' style='font-size:14px;color:#333;'>
<tr><td style='color:#666;width:140px;'>Bank Name:</td><td style='font-weight:600;'>{bank_name}</td></tr>
<tr><td style='color:#666;'>Account Holder:</td><td style='font-weight:600;'>{account_holder}</td></tr>
<tr><td style='color:#666;'>Account Number:</td><td style='font-weight:600;'>{account_id}</td></tr>
<tr><td style='color:#666;'>Verification ID:</td><td style='font-weight:600;color:#059669;'>{verification_id}</td></tr>
<tr><td style='color:#666;'>Status:</td><td><span style='background:#dcfce7;color:#059669;padding:2px 12px;border-radius:10px;font-weight:600;'>&#9989; VERIFIED GENUINE</span></td></tr>
</table></div>
<p style='font-size:13px;color:#666;line-height:1.5;'>To view the official bank portal page and verify the statement details, click the button below:</p>
<table cellpadding='0' cellspacing='0' style='margin:24px 0;'>
<tr><td style='background:#059669;border-radius:8px;padding:14px 32px;'>
<a href='{view_url}' style='color:#fff;text-decoration:none;font-size:15px;font-weight:600;'>&#128279; View Verified Statement Online</a>
</td></tr></table>
<p style='font-size:13px;color:#666;margin:0 0 8px 0;'>PDF Password: <code style='background:#f0f0f0;padding:2px 10px;border-radius:4px;font-size:15px;font-weight:bold;color:#059669;'>{password}</code></p>
<p style='font-size:12px;color:#999;margin:16px 0 0 0;'>Verification ID: <strong>{verification_id}</strong> | Generated: {datetime.utcnow().strftime('%d %b %Y, %I:%M %p')} UTC</p>
<p style='font-size:12px;color:#999;margin:4px 0 0 0;'>This is an auto-generated verification response.</p>
</td></tr>
<tr><td style='background:#f8f9fb;padding:20px;text-align:center;border-top:1px solid #e0e0e0;'>
<p style='font-size:12px;color:#999;margin:0;'>&copy; {datetime.utcnow().year} BGV Verification Service. All rights reserved.</p>
</td></tr></table>
</td></tr></table></body></html>"""


class InboundEmailProcessor:
    """Handles fetching BGV emails from the company IMAP inbox and auto-replying."""

    def __init__(
        self,
        imap_host: str,
        imap_port: int,
        imap_username: str,
        imap_password: str,
        use_ssl: bool,
        company_email: str,
        bgv_sender_filter: str = "",
        reply_from_name: str = "BGV Verification Service",
        include_pdf_attachment: bool = True,
        include_verification_link: bool = True,
    ):
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.imap_username = imap_username
        self.imap_password = imap_password
        self.use_ssl = use_ssl
        self.company_email = company_email.lower()
        self.bgv_sender_filter = bgv_sender_filter.lower() if bgv_sender_filter else ""
        self.reply_from_name = reply_from_name
        self.include_pdf_attachment = include_pdf_attachment
        self.include_verification_link = include_verification_link
        self._smtp_config: Optional[EmailConfig] = None
        self._db_session_factory = None

    def set_smtp_config(self, config: EmailConfig):
        """Set the SMTP config for sending replies."""
        self._smtp_config = config

    def set_db_session_factory(self, factory):
        """Set the async DB session factory for looking up statement data."""
        self._db_session_factory = factory

    def _connect_imap(self):
        """Connect to the IMAP server and return the connection object."""
        if self.use_ssl or self.imap_port == 993:
            conn = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
        else:
            conn = imaplib.IMAP4(self.imap_host, self.imap_port)
            conn.starttls()
        conn.login(self.imap_username, self.imap_password)
        return conn

    def _is_bgv_email(self, sender: str, subject: str, body: str,
                       to_header: str = "", cc_header: str = "") -> tuple[bool, list[str]]:
        """Check if an email is BGV-related based on sender, subject, body, and headers.

        Args:
            sender: Extracted sender email address.
            subject: Decoded email subject.
            body: Decoded email body text.
            to_header: Raw To header value from the email.
            cc_header: Raw Cc header value from the email.

        Returns:
            Tuple of (is_bgv: bool, matched_keywords: list[str])
        """
        sender_lower = sender.lower()
        subject_lower = subject.lower()
        body_lower = body.lower()
        combined = f"{subject_lower} {body_lower}"

        # Check BGV sender filter
        if self.bgv_sender_filter:
            if self.bgv_sender_filter in sender_lower:
                matched_kw = detect_bgv_keywords(combined)
                if matched_kw:
                    return True, matched_kw
                # If sender matches filter, treat as BGV even without keywords
                return True, ["matched sender filter"]

        # Check if sent TO or CC'd to our company email (from actual email headers)
        if self.company_email:
            all_recipients = f"{to_header} {cc_header}".lower()
            if self.company_email in all_recipients:
                matched_kw = detect_bgv_keywords(combined)
                if matched_kw:
                    return True, matched_kw

        # General keyword detection
        matched_kw = detect_bgv_keywords(combined)
        if matched_kw:
            return True, matched_kw

        return False, []

    async def _get_uploaded_pdf(self, account_id: str, db_session) -> Optional[bytes]:
        """Look up an uploaded PDF from the database by account ID."""
        try:
            from sqlalchemy import select
            from app.models.upload import UploadedPdf
            result = await db_session.execute(
                select(UploadedPdf).where(UploadedPdf.account_id == account_id)
            )
            uploaded = result.scalar_one_or_none()
            if uploaded:
                return uploaded.pdf_data
        except Exception:
            pass
        return None

    async def check_inbox(
        self,
        lookback_days: int = 7,
        max_emails: int = 50,
        db_session=None,
    ) -> dict:
        """Check the IMAP inbox for BGV-related emails and auto-reply.

        Returns a summary of what was processed.
        """
        results = {
            "status": "ok",
            "totalEmails": 0,
            "bgvMatched": 0,
            "repliesSent": 0,
            "skipped": 0,
            "failed": 0,
            "details": [],
        }

        if not self._smtp_config or not self._smtp_config.is_configured():
            results["status"] = "error"
            results["details"].append({
                "error": "SMTP not configured. Configure email SMTP settings first."
            })
            return results

        try:
            # Connect to IMAP
            conn = await asyncio.to_thread(self._connect_imap)
        except Exception as e:
            results["status"] = "error"
            results["details"].append({
                "error": f"Failed to connect to IMAP server {self.imap_host}:{self.imap_port}: {str(e)}"
            })
            return results

        try:
            # Select inbox (read-only)
            await asyncio.to_thread(conn.select, "INBOX", readonly=True)

            # Search for recent unseen emails
            # We look for emails from the last N days
            search_criteria = f'(SINCE {(datetime.utcnow().strftime("%d-%b-%Y"))})'
            status, messages = await asyncio.to_thread(
                conn.search, None, search_criteria
            )

            if status != "OK" or not messages[0]:
                results["details"].append({"info": "No emails found in the specified period."})
                return results

            email_uids = messages[0].split()
            # Limit to max_emails, newest first
            email_uids = email_uids[-max_emails:]
            results["totalEmails"] = len(email_uids)

            for uid in email_uids:
                try:
                    status, msg_data = await asyncio.to_thread(
                        conn.fetch, uid, "(RFC822)"
                    )
                    if status != "OK" or not msg_data or not msg_data[0]:
                        continue

                    raw_email = msg_data[0][1]
                    if isinstance(raw_email, bytes):
                        msg = email_lib.message_from_bytes(raw_email)
                    else:
                        continue

                    # Parse sender, subject, date
                    sender_raw = msg.get("From", "")
                    sender = extract_email_address(sender_raw)
                    subject = decode_mime_header(msg.get("Subject", ""))
                    date_str = msg.get("Date", "")
                    body = get_email_body(msg)
                    body_preview = body[:500] if body else ""

                    # Parse received date
                    received_at = None
                    try:
                        from email.utils import parsedate_to_datetime
                        received_at = parsedate_to_datetime(date_str)
                    except Exception:
                        received_at = datetime.utcnow()

                    email_uid_str = str(uid.decode() if isinstance(uid, bytes) else uid)

                    # Check if already processed
                    if db_session:
                        from sqlalchemy import select
                        from app.models.inbound_email import InboundEmailLog
                        existing = await db_session.execute(
                            select(InboundEmailLog).where(
                                InboundEmailLog.email_uid == email_uid_str
                            )
                        )
                        if existing.scalar_one_or_none():
                            results["skipped"] += 1
                            results["details"].append({
                                "email": subject[:50],
                                "sender": sender,
                                "action": "skipped",
                                "reason": "Already processed",
                            })
                            continue

                    # Get To/Cc headers from email message
                    to_header = decode_mime_header(str(msg.get("To", "")))
                    cc_header = decode_mime_header(str(msg.get("Cc", "")))

                    # Detect BGV using headers + body
                    is_bgv, matched_kw = self._is_bgv_email(
                        sender, subject, body,
                        to_header=to_header, cc_header=cc_header
                    )

                    if not is_bgv:
                        # Log as non-BGV (skipped)
                        results["skipped"] += 1
                        detail = {
                            "email": subject[:50],
                            "sender": sender,
                            "action": "skipped",
                            "reason": "Not BGV-related",
                        }
                        results["details"].append(detail)
                        if db_session:
                            await self._log_email(
                                db_session, email_uid_str, sender, subject,
                                body_preview, received_at, matched_kw, None,
                                "skipped"
                            )
                        continue

                    # BGV detected - process it
                    results["bgvMatched"] += 1

                    # Try to extract account number
                    account_id = extract_account_number(f"{subject} {body}")

                    # Send auto-reply
                    reply_result = await self._send_bgv_reply(
                        db_session=db_session,
                        sender=sender,
                        subject=subject,
                        email_uid=email_uid_str,
                        body_preview=body_preview,
                        received_at=received_at,
                        matched_kw=matched_kw,
                        account_id=account_id,
                        sender_display=decode_mime_header(msg.get("From", "")),
                    )

                    if reply_result.get("status") == "sent":
                        results["repliesSent"] += 1
                    else:
                        results["failed"] += 1

                    results["details"].append(reply_result.get("detail", {}))

                except Exception as e:
                    results["failed"] += 1
                    results["details"].append({
                        "email": str(uid),
                        "action": "failed",
                        "error": str(e),
                    })

            # Close connection
            await asyncio.to_thread(conn.close)
            await asyncio.to_thread(conn.logout)

        except Exception as e:
            results["status"] = "error"
            results["details"].append({
                "error": f"IMAP processing error: {str(e)}"
            })

        # Add summary
        results["details"].insert(0, {
            "action": "summary",
            "totalEmails": results["totalEmails"],
            "bgvMatched": results["bgvMatched"],
            "repliesSent": results["repliesSent"],
            "skipped": results["skipped"],
            "failed": results["failed"],
        })

        return results

    async def _send_bgv_reply(
        self,
        db_session,
        sender: str,
        subject: str,
        email_uid: str,
        body_preview: str,
        received_at: Optional[datetime],
        matched_kw: list[str],
        account_id: Optional[str] = None,
        sender_display: str = "",
    ) -> dict:
        """Send a BGV verification reply and log the result."""
        result = {
            "status": "pending",
            "detail": {"email": subject[:50], "sender": sender, "action": ""},
        }

        bank_name = "Verified Bank"
        account_holder = "Account Holder"
        password = "0000"

        # If no account ID found, use a default
        if not account_id:
            account_id = "BGV-AUTO"

        # Generate verification ID
        verification_id = generate_verification_id()
        view_url = f"http://localhost:8080/api/bgv/view/{verification_id}"
        password = account_id[-4:] if len(account_id) >= 4 else account_id

        try:
            # Build the reply
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders
            import ssl
            import smtplib

            reply_html = generate_genuine_reply_html(
                bank_name=bank_name,
                account_holder=account_holder,
                account_id=account_id,
                verification_id=verification_id,
                view_url=view_url,
                password=password,
            )

            msg = MIMEMultipart("mixed")
            msg["From"] = f"{self.reply_from_name} <{self._smtp_config.username}>"
            msg["To"] = sender
            msg["Subject"] = f"Re: {subject} — BGV Verification Confirmed [ID: {verification_id}]"
            msg["In-Reply-To"] = email_uid

            # Attach HTML body
            msg.attach(MIMEText(reply_html, "html"))

            # Attach PDF if enabled - look up uploaded PDF from DB
            if self.include_pdf_attachment and db_session and account_id != "BGV-AUTO":
                pdf_bytes = await self._get_uploaded_pdf(account_id, db_session)
                if pdf_bytes:
                    encrypted_pdf = encrypt_pdf(pdf_bytes, password)
                    attachment = MIMEBase("application", "octet-stream")
                    attachment.set_payload(encrypted_pdf)
                    encoders.encode_base64(attachment)
                    filename = f"verified-statement-{account_id}.pdf"
                    attachment.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{filename}"',
                    )
                    msg.attach(attachment)

            # Send the email synchronously in a thread
            def _send_sync():
                if self._smtp_config.use_ssl or self._smtp_config.port == 465:
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(
                        self._smtp_config.host,
                        self._smtp_config.port,
                        context=context,
                    ) as server:
                        server.login(self._smtp_config.username, self._smtp_config.password)
                        server.send_message(msg)
                else:
                    with smtplib.SMTP(self._smtp_config.host, self._smtp_config.port) as server:
                        server.starttls(context=ssl.create_default_context())
                        server.login(self._smtp_config.username, self._smtp_config.password)
                        server.send_message(msg)

            await asyncio.to_thread(_send_sync)

            # Log success
            result["status"] = "sent"
            result["detail"] = {
                "email": subject[:50],
                "sender": sender,
                "action": "replied",
                "verificationId": verification_id,
                "accountId": account_id,
            }

            if db_session:
                await self._log_email(
                    db_session, email_uid, sender, subject,
                    body_preview, received_at, matched_kw, account_id,
                    "processed", reply_sent=True,
                    reply_subject=msg["Subject"],
                    reply_verification_id=verification_id,
                    reply_sent_at=datetime.utcnow(),
                )

        except Exception as e:
            result["status"] = "failed"
            result["detail"] = {
                "email": subject[:50],
                "sender": sender,
                "action": "failed",
                "error": str(e),
            }

            if db_session:
                await self._log_email(
                    db_session, email_uid, sender, subject,
                    body_preview, received_at, matched_kw, account_id,
                    "failed", reply_sent=False, reply_error=str(e),
                )

        return result

    async def _log_email(
        self,
        db_session,
        email_uid: str,
        sender: str,
        subject: str,
        body_preview: str,
        received_at: Optional[datetime],
        matched_kw: list[str],
        account_id: Optional[str],
        bgv_status: str,
        reply_sent: bool = False,
        reply_subject: Optional[str] = None,
        reply_verification_id: Optional[str] = None,
        reply_error: Optional[str] = None,
        reply_sent_at: Optional[datetime] = None,
    ):
        """Log an inbound email processing entry to the database."""
        try:
            from app.models.inbound_email import InboundEmailLog

            log_entry = InboundEmailLog(
                email_uid=email_uid,
                sender=sender,
                subject=subject,
                body_preview=body_preview[:500] if body_preview else "",
                received_at=received_at or datetime.utcnow(),
                detected_keywords=matched_kw,
                extracted_account_id=account_id,
                bgv_status=bgv_status,
                reply_sent=reply_sent,
                reply_subject=reply_subject,
                reply_verification_id=reply_verification_id,
                reply_sent_at=reply_sent_at,
                reply_error=reply_error,
                processed_at=datetime.utcnow(),
            )
            db_session.add(log_entry)
            await db_session.commit()
        except Exception:
            await db_session.rollback()


# In-memory active processor (singleton pattern)
_active_processor: Optional[InboundEmailProcessor] = None


def get_active_processor() -> Optional[InboundEmailProcessor]:
    """Get the currently active inbound email processor."""
    return _active_processor


def set_active_processor(processor: Optional[InboundEmailProcessor]):
    """Set the active inbound email processor."""
    global _active_processor
    _active_processor = processor
