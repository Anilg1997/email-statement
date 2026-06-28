"""Email sending service — async SMTP with PDF attachment.

Uses aiosmtplib for non-blocking SMTP operations.
"""
import asyncio
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from typing import Optional


class EmailConfig:
    def __init__(self, host: str, port: int, username: str, password: str,
                 use_ssl: bool = True, from_name: str = "Bank Statement Service"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.from_name = from_name

    def is_configured(self) -> bool:
        return bool(self.host and self.username and self.password)


async def send_statement_email(
    config: EmailConfig,
    to_email: str,
    bank_name: str,
    account_holder: str,
    account_id: str,
    pdf_bytes: bytes,
    password: str,
) -> dict:
    """Send an email with the PDF attachment using SMTP (async).

    Uses synchronous smtplib wrapped in asyncio.to_thread() to avoid blocking
    the event loop. For truly async SMTP, aiosmtplib is also an option.
    """
    if not config.is_configured():
        return {"status": "error", "message": "Email is not configured."}

    def _mask_account(acct: str) -> str:
        if not acct or len(acct) < 4:
            return acct or ""
        return "X" * (len(acct) - 4) + acct[-4:]

    masked_acct = _mask_account(account_id)

    msg = MIMEMultipart("mixed")
    msg["From"] = f"{config.from_name} <{config.username}>"
    msg["To"] = to_email
    msg["Subject"] = f"Your {bank_name} Account Statement - {masked_acct}"

    # HTML body
    html_body = f"""<!DOCTYPE html>
<html><body style='font-family:Arial,sans-serif;padding:20px;'>
<div style='max-width:600px;margin:0 auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;'>
<div style='background:linear-gradient(135deg,#0a1628,#1a1a3e);padding:24px;text-align:center;'>
<h2 style='color:#fff;margin:0;'>{bank_name}</h2>
<p style='color:#8899bb;font-size:13px;margin:4px 0 0 0;'>Secure Statement Delivery</p>
</div>
<div style='padding:24px;'>
<p style='font-size:15px;color:#333;'>Dear <strong>{account_holder}</strong>,</p>
<p style='font-size:14px;color:#555;line-height:1.6;'>Please find attached your account statement for <strong>{bank_name}</strong> (Account: {masked_acct}).</p>
<div style='background:#f0f7ff;border:1px solid #cce5ff;border-radius:8px;padding:16px;margin:20px 0;'>
<p style='font-size:13px;color:#555;margin:0 0 8px 0;'><strong>Statement Details:</strong></p>
<table width='100%' cellpadding='4' cellspacing='0' style='font-size:13px;color:#555;'>
<tr><td style='color:#999;width:120px;'>Account Holder:</td><td style='font-weight:600;'>{account_holder}</td></tr>
<tr><td style='color:#999;'>Account Number:</td><td style='font-weight:600;'>{masked_acct}</td></tr>
<tr><td style='color:#999;'>PDF Password:</td><td style='font-weight:600;color:#2563eb;'>{password}</td></tr>
</table></div>
<p style='font-size:13px;color:#666;line-height:1.5;'>The statement PDF is password-protected. Use the last 4 digits of your account number (<strong>{password}</strong>) to open it.</p>
<p style='font-size:13px;color:#999;line-height:1.5;margin:20px 0 0 0;'>This is an automated message from {bank_name}. Please do not reply to this email.</p>
</div>
<div style='background:#f8f9fb;padding:16px;text-align:center;border-top:1px solid #e0e0e0;'>
<p style='font-size:12px;color:#999;margin:0;'>&copy; 2024 {bank_name}. All rights reserved.</p>
</div>
</div></body></html>"""

    msg.attach(MIMEText(html_body, "html"))

    # Attach PDF
    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(pdf_bytes)
    encoders.encode_base64(attachment)
    filename = f"statement-{account_id}.pdf"
    attachment.add_header("Content-Disposition", f"attachment; filename={filename}")
    msg.attach(attachment)

    def _send_sync():
        import smtplib
        if config.use_ssl or config.port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(config.host, config.port, context=context) as server:
                server.login(config.username, config.password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(config.host, config.port) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(config.username, config.password)
                server.send_message(msg)

    try:
        # Run synchronous SMTP in a thread to avoid blocking event loop
        await asyncio.to_thread(_send_sync)
        return {
            "status": "ok",
            "message": f"Email sent successfully to {to_email}",
            "to": to_email,
            "subject": msg["Subject"],
            "attachment": filename,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to send email: {str(e)}"}
