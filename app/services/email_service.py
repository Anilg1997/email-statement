"""Email sending service — async SMTP with PDF attachment.

Uses aiosmtplib for non-blocking SMTP operations.
"""
import asyncio
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders



class EmailConfig:
    def __init__(self, host: str, port: int, username: str, password: str,
                 use_ssl: bool = True, **kwargs):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        # Store from_name for backward compatibility (used by API layer)
        self.from_name = kwargs.get("from_name", "")

    def is_configured(self) -> bool:
        return bool(self.host and self.username and self.password)


async def send_statement_email(
    config: EmailConfig,
    to_email: str,
    bank_name: str,
    account_id: str,
    pdf_bytes: bytes,
) -> dict:
    """Send an email with the PDF attachment using SMTP (async).

    The email appears to come from the bank (noreply@bankname.com).
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
    # Use bank name as the sender display name
    msg["From"] = f"{bank_name.upper()} Statement"
    msg["To"] = to_email
    msg["Subject"] = f"Account Statement from {bank_name} - {masked_acct}"

    # HTML body with bank branding
    html_body = f"""<!DOCTYPE html>
<html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'></head>
<body style='margin:0;padding:0;background:#f4f6f8;font-family:Arial,Helvetica,sans-serif;'>
<table width='100%' cellpadding='0' cellspacing='0' style='background:#f4f6f8;padding:20px;'>
<tr><td align='center'>
<table width='600' cellpadding='0' cellspacing='0' style='background:#fff;border-radius:4px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);'>

<!-- HDFC Bank Header Banner -->
<tr><td style='background:#004B8D;padding:20px 30px;text-align:left;'>
<table width='100%' cellpadding='0' cellspacing='0'><tr>
<td style='width:50%;'>
<div style='font-size:24px;font-weight:bold;color:#fff;letter-spacing:1px;'>HDFC BANK</div>
<div style='font-size:11px;color:#b3d4ff;margin-top:4px;'>We understand your world</div>
</td>
<td style='width:50%;text-align:right;'>
<div style='font-size:10px;color:#b3d4ff;'>Secure Document Delivery</div>
</td>
</tr></table>
</td></tr>

<!-- Body -->
<tr><td style='padding:30px;'>
<p style='font-size:13px;color:#333;line-height:1.6;margin:0 0 12px 0;'>As per request, please find attached your <strong>{bank_name}</strong> account statement for the account ending with <strong>{masked_acct[-4:]}</strong>.</p>

<!-- Account Details Table -->
<table width='100%' cellpadding='8' cellspacing='0' style='font-size:12px;color:#333;border:1px solid #ddd;margin:16px 0;'>
<tr style='background:#f0f5fa;'><td style='width:150px;font-weight:600;border-bottom:1px solid #ddd;'>Account Number</td><td style='border-bottom:1px solid #ddd;'>{masked_acct}</td></tr>
<tr><td style='font-weight:600;border-bottom:1px solid #ddd;'>Statement Period</td><td style='border-bottom:1px solid #ddd;'>Latest Statement</td></tr>
<tr style='background:#f0f5fa;'><td style='font-weight:600;border-bottom:1px solid #ddd;'>Document Type</td><td style='border-bottom:1px solid #ddd;'>e-Statement (PDF)</td></tr>
</table>

<p style='font-size:12px;color:#555;line-height:1.5;margin:16px 0;'>The attached PDF is password protected with the last 4 digits of your account number.</p>

<p style='font-size:12px;color:#555;line-height:1.5;margin:16px 0;'>If you have any queries, please contact our 24x7 PhoneBanking at <strong>1800 266 4332</strong> or visit your nearest {bank_name} branch.</p>

<p style='font-size:12px;color:#555;line-height:1.5;margin:16px 0 0 0;'>Warm Regards,<br/><strong>Customer Service Team</strong><br/>{bank_name}</p>
</td></tr>

<!-- Footer -->
<tr><td style='background:#004B8D;padding:16px 30px;text-align:center;border-top:2px solid #003366;'>
<p style='font-size:10px;color:#b3d4ff;margin:0 0 4px 0;'>This is a system generated e-mail. Please do not reply to this message.</p>
<p style='font-size:10px;color:#b3d4ff;margin:0 0 4px 0;'>HDFC Bank Ltd. | {bank_name} House, 165-166, Backbay Reclamation, Mumbai 400 020</p>
<p style='font-size:10px;color:#b3d4ff;margin:0;'>&copy; 2024 {bank_name} Ltd. All rights reserved.</p>
</td></tr>

</table>
</td></tr></table></body></html>"""

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
        if config.port == 465:
            # Port 465 uses implicit SSL/TLS
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(config.host, config.port, context=context) as server:
                server.login(config.username, config.password)
                server.send_message(msg)
        else:
            # Port 587 and others use STARTTLS (connect plain, then upgrade)
            with smtplib.SMTP(config.host, config.port) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
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
