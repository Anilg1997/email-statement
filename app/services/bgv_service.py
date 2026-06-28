"""BGV (Background Verification) service — verification links, portal viewer, email templates."""
import uuid
from datetime import datetime
from typing import Optional


def generate_verification_id() -> str:
    token = uuid.uuid4().hex[:16].upper()
    return f"BGV-{token}"


def generate_token() -> str:
    return uuid.uuid4().hex[:8].upper()


def mask_account_number(account_number: str) -> str:
    if not account_number or len(account_number) < 4:
        return account_number or ""
    return "X" * (len(account_number) - 4) + account_number[-4:]


def escape_html(s: Optional[str]) -> str:
    if not s:
        return ""
    return (s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def generate_bank_portal_page(
    bank_name: str,
    account_holder: str,
    account_number: str,
    period: str,
    branch: str,
    ifsc: str,
    address: str,
    opening_balance: str,
    closing_balance: str,
    total_debits: str,
    total_credits: str,
    transactions: list,
    password: str,
    verification_id: str,
) -> str:
    """Generate a realistic bank net-banking portal HTML page."""
    masked = mask_account_number(account_number)
    current_date = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")

    # Build transaction rows
    txn_rows = ""
    if not transactions:
        txn_rows = "<tr><td colspan='4' style='text-align:center;padding:20px;color:#999;'>No transactions found</td></tr>"
    else:
        for i, txn in enumerate(transactions[:50]):
            bg = "#f8f9fb" if i % 2 == 0 else "#ffffff"
            date = txn.get("date", "-")
            desc = txn.get("description", "-")
            debit = txn.get("debit", "")
            credit_s = txn.get("credit", "")
            debit_style = "#dc2626" if debit else "#999"
            credit_style = "#16a34a" if credit_s else "#999"

            debit_cell = f"<span style='background:#fef2f2;padding:2px 8px;border-radius:4px;'>\u20B9 {escape_html(debit)}</span>" if debit else "-"
            credit_cell = f"<span style='background:#f0fdf4;padding:2px 8px;border-radius:4px;'>\u20B9 {escape_html(credit_s)}</span>" if credit_s else "-"

            txn_rows += (
                f"<tr style='background:{bg};'>"
                f"<td style='padding:10px 12px;border-bottom:1px solid #eee;font-size:13px;color:#555;'>{escape_html(date)}</td>"
                f"<td style='padding:10px 12px;border-bottom:1px solid #eee;font-size:13px;color:#333;'>{escape_html(desc)}</td>"
                f"<td style='padding:10px 12px;border-bottom:1px solid #eee;font-size:13px;text-align:right;color:{debit_style};'>{debit_cell}</td>"
                f"<td style='padding:10px 12px;border-bottom:1px solid #eee;font-size:13px;text-align:right;color:{credit_style};'>{credit_cell}</td>"
                f"</tr>"
            )

    year = datetime.utcnow().year

    return f"""<!DOCTYPE html>
<html lang='en'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>
<title>{escape_html(bank_name)} - Account Statement</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;}}
body{{background:#f0f2f5;color:#333;}}
.top-bar{{background:linear-gradient(135deg,#0a1628 0%,#1a1a3e 100%);color:#fff;padding:0 40px;height:64px;display:flex;align-items:center;justify-content:space-between;}}
.top-bar .bank-logo{{display:flex;align-items:center;gap:12px;}}
.top-bar .bank-logo .logo-icon{{width:40px;height:40px;background:linear-gradient(135deg,#4a9eff,#2563eb);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;}}
.top-bar .bank-name{{font-size:20px;font-weight:700;}}
.top-bar .bank-tagline{{font-size:11px;color:#8899bb;}}
.top-bar .secure-badge{{display:flex;align-items:center;gap:8px;background:rgba(255,255,255,0.1);padding:8px 16px;border-radius:8px;font-size:12px;color:#aabbdd;}}
.nav-bar{{background:#fff;border-bottom:1px solid #e0e0e0;padding:0 40px;display:flex;gap:0;}}
.nav-bar .nav-item{{padding:14px 24px;font-size:13px;font-weight:600;color:#666;border-bottom:3px solid transparent;cursor:default;}}
.nav-bar .nav-item.active{{color:#2563eb;border-bottom-color:#2563eb;}}
.container{{max-width:1100px;margin:24px auto;padding:0 20px;}}
.welcome-bar{{background:linear-gradient(135deg,#2563eb,#1d4ed8);border-radius:12px;padding:24px 32px;color:#fff;margin-bottom:24px;display:flex;justify-content:space-between;align-items:center;}}
.welcome-bar h1{{font-size:22px;font-weight:700;}}
.welcome-bar p{{font-size:13px;opacity:0.9;margin-top:4px;}}
.welcome-bar .visit-info{{text-align:right;font-size:12px;opacity:0.8;}}
.card{{background:#fff;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,0.06);margin-bottom:20px;overflow:hidden;}}
.card-header{{padding:16px 24px;border-bottom:1px solid #f0f0f0;display:flex;align-items:center;justify-content:space-between;}}
.card-header h2{{font-size:16px;font-weight:600;color:#1a1a2e;}}
.card-body{{padding:20px 24px;}}
.info-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;}}
.info-item .label{{font-size:11px;color:#999;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;}}
.info-item .value{{font-size:15px;color:#333;font-weight:500;}}
table{{width:100%;border-collapse:collapse;}}
th{{padding:12px 12px;font-size:11px;font-weight:600;color:#666;text-align:left;border-bottom:2px solid #e0e0e0;text-transform:uppercase;letter-spacing:0.5px;}}
.summary-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;}}
.summary-item{{padding:20px;border-radius:10px;text-align:center;}}
.summary-item .amount{{font-size:24px;font-weight:700;margin-top:4px;}}
.summary-item .label{{font-size:12px;opacity:0.8;}}
.summary-item.opening{{background:#f0f7ff;color:#2563eb;}}
.summary-item.debits{{background:#fef2f2;color:#dc2626;}}
.summary-item.credits{{background:#f0fdf4;color:#16a34a;}}
.summary-item.closing{{background:#f5f3ff;color:#7c3aed;}}
.footer-bar{{background:#0a1628;color:#8899bb;padding:20px 40px;text-align:center;font-size:12px;}}
.verify-banner{{background:#fefce8;border:1px solid #fde68a;border-radius:8px;padding:12px 16px;margin-bottom:20px;display:flex;align-items:center;gap:12px;font-size:13px;color:#92400e;}}
</style></head><body>
<div class='top-bar'>
<div class='bank-logo'><div class='logo-icon'>{escape_html(bank_name[0])}</div><div><div class='bank-name'>{escape_html(bank_name)}</div><div class='bank-tagline'>NetBanking Portal</div></div></div>
<div class='secure-badge'>\U0001f512 SECURE | {escape_html(current_date)}</div>
</div>
<div class='nav-bar'>
<div class='nav-item active'>Account Summary</div><div class='nav-item'>Statements</div><div class='nav-item'>Transactions</div><div class='nav-item'>Downloads</div><div class='nav-item'>Settings</div>
</div>
<div class='container'>
<div class='verify-banner'>\u2705 <div><strong>Verified Statement</strong> &mdash; Official bank statement (ID: {escape_html(verification_id)})</div></div>
<div class='welcome-bar'>
<div><h1>Account Statement</h1><p>{escape_html(bank_name)} | Account: {escape_html(masked)}</p></div>
<div class='visit-info'><div>Visit ID: {escape_html(verification_id)}</div><div>Generated: {escape_html(current_date)}</div></div>
</div>
<div class='card'>
<div class='card-header'><h2>Account Information</h2><span class='badge'>{escape_html(period)}</span></div>
<div class='card-body'>
<div class='info-grid'>
<div class='info-item'><div class='label'>Account Number</div><div class='value'>{escape_html(masked)}</div></div>
<div class='info-item'><div class='label'>Branch</div><div class='value'>{escape_html(branch)}</div></div>
<div class='info-item'><div class='label'>IFSC Code</div><div class='value'>{escape_html(ifsc)}</div></div>
<div class='info-item'><div class='label'>Address</div><div class='value'>{escape_html(address)}</div></div>
<div class='info-item'><div class='label'>Statement Period</div><div class='value'>{escape_html(period)}</div></div>
</div></div></div>
<div class='summary-grid'>
<div class='summary-item opening'><div class='label'>Opening Balance</div><div class='amount'>\u20B9 {escape_html(opening_balance)}</div></div>
<div class='summary-item debits'><div class='label'>Total Debits</div><div class='amount'>\u20B9 {escape_html(total_debits)}</div></div>
<div class='summary-item credits'><div class='label'>Total Credits</div><div class='amount'>\u20B9 {escape_html(total_credits)}</div></div>
<div class='summary-item closing'><div class='label'>Closing Balance</div><div class='amount'>\u20B9 {escape_html(closing_balance)}</div></div>
</div>
<div class='card' style='margin-top:20px;'>
<div class='card-header'><h2>Transaction History</h2><span class='badge'>{len(transactions)} entries</span></div>
<div class='card-body p-0'>
<table><thead><tr><th>Date</th><th>Description</th><th style='text-align:right;'>Debit (\u20B9)</th><th style='text-align:right;'>Credit (\u20B9)</th></tr></thead><tbody>{txn_rows}</tbody></table>
</div></div>
<div class='card'>
<div class='card-header'><h2>Download Statement</h2><span class='badge'>Password Protected</span></div>
<div class='card-body' style='display:flex;align-items:center;justify-content:space-between;'>
<div><strong>Statement PDF</strong><br><span style='font-size:13px;color:#999;'>Use last 4 digits of account number to open</span></div>
<a href='/api/replace?accountId={escape_html(account_number)}' target='_blank' style='background:#2563eb;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:600;'>\u2b07 Download PDF</a>
</div></div>
</div>
<div class='footer-bar'>
<p>{escape_html(bank_name)} NetBanking | \u00a9 {year} All Rights Reserved</p>
</div>
</body></html>"""


def generate_email_html(
    bank_name: str,
    account_holder: str,
    account_id: str,
    view_url: str,
    password: str,
) -> str:
    """Generate a bank-like email HTML template."""
    masked = mask_account_number(account_id)
    current_date = datetime.utcnow().strftime("%d %b %Y")

    return f"""<!DOCTYPE html>
<html><head><meta charset='UTF-8'></head>
<body style='margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;'>
<table width='100%' cellpadding='0' cellspacing='0' style='background:#f5f5f5;padding:20px;'>
<tr><td align='center'>
<table width='600' cellpadding='0' cellspacing='0' style='background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);'>
<tr><td style='background:linear-gradient(135deg,#0a1628,#1a1a3e);padding:30px;text-align:center;'>
<div style='font-size:28px;font-weight:bold;color:#fff;'>{escape_html(bank_name)}</div>
<div style='font-size:13px;color:#8899bb;margin-top:4px;'>Secure Account Statement</div>
</td></tr>
<tr><td style='padding:30px;'>
<p style='font-size:14px;color:#555;line-height:1.6;margin:0 0 16px 0;'>Please find attached your account statement for <strong>{escape_html(bank_name)}</strong> (Account: {escape_html(masked)}).</p>
<div style='background:#f0f7ff;border:1px solid #cce5ff;border-radius:8px;padding:16px;margin:20px 0;'>
<p style='font-size:13px;color:#555;margin:0 0 8px 0;'><strong>Statement Details:</strong></p>
<table width='100%' cellpadding='4' cellspacing='0' style='font-size:13px;color:#555;'>
<tr><td style='color:#999;width:120px;'>Account Number:</td><td style='font-weight:600;'>{escape_html(masked)}</td></tr>
<tr><td style='color:#999;'>Date Generated:</td><td style='font-weight:600;'>{escape_html(current_date)}</td></tr>
</table></div>
<p style='font-size:13px;color:#666;'>The statement PDF is password-protected (last 4 digits of account number).</p>
<table cellpadding='0' cellspacing='0' style='margin:24px 0;'>
<tr><td style='background:#2563eb;border-radius:8px;padding:14px 32px;'>
<a href='{escape_html(view_url)}' style='color:#fff;text-decoration:none;font-size:15px;font-weight:600;'>\U0001f4c4 View Statement Online</a>
</td></tr></table>
<p style='font-size:13px;color:#999;margin:16px 0 0 0;'>This is an automated message. Please do not reply.</p>
</td></tr>
<tr><td style='background:#f8f9fb;padding:20px;text-align:center;border-top:1px solid #e0e0e0;'>
<p style='font-size:12px;color:#999;margin:0;'>&copy; 2024 {escape_html(bank_name)}. All rights reserved.</p>
</td></tr></table>
</td></tr></table></body></html>"""
