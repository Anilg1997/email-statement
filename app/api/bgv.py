from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from app.schemas.bgv import BGVGenerateRequest, BGVEmailTemplateRequest
from app.services.bgv_service import (
    generate_verification_id, generate_token, generate_bank_portal_page,
    generate_email_html,
)
from app.database import get_session
from app.models.verification import VerificationLink
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/bgv", tags=["bgv"])

# In-memory statement store (replaces SavedStatement model)
_statement_store: dict[str, dict] = {}


@router.post("/store-statement")
async def store_statement(data: dict):
    """Store statement data for BGV verification (in-memory storage)."""
    account_number = data.get("accountNumber", "0000")
    _statement_store[account_number] = data
    return {"status": "ok", "token": "stored", "message": "Statement stored for verification"}


@router.post("/generate-link")
async def generate_verification_link(
    req: BGVGenerateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Generate a BGV verification link."""
    if not req.accountId:
        raise HTTPException(status_code=400, detail="accountId required")

    verification_id = generate_verification_id()
    link = VerificationLink(
        verification_id=verification_id,
        account_id=req.accountId,
        bank_name=req.bankName,
        account_holder=req.accountHolder,
        mode=req.mode,
        status="active",
        access_count=0,
        created_at=datetime.utcnow(),
    )
    session.add(link)
    await session.commit()

    base_url = "http://localhost:8080"
    view_url = f"{base_url}/api/bgv/view/{verification_id}"
    password = req.accountId[-4:] if len(req.accountId) >= 4 else req.accountId

    return {
        "status": "ok",
        "verificationId": verification_id,
        "token": generate_token(),
        "viewUrl": view_url,
        "createdAt": link.created_at.isoformat() if link.created_at else datetime.utcnow().isoformat(),
        "password": password,
        "mode": req.mode,
    }


@router.get("/view/{verification_id}", response_class=HTMLResponse)
async def view_verification(
    verification_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Serve the bank portal viewer page for a verification link."""
    result = await session.execute(
        select(VerificationLink).where(VerificationLink.verification_id == verification_id)
    )
    link = result.scalar_one_or_none()

    if not link:
        return HTMLResponse(
            content="""<!DOCTYPE html><html><head><title>Invalid Link</title>
            <style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;background:#f5f5f5;}
            .card{text-align:center;padding:40px;background:#fff;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
            h1{color:#dc2626;}p{color:#666;}</style></head><body>
            <div class='card'><h1>Invalid Verification Link</h1><p>This link is invalid or has expired.</p></div></body></html>""",
            status_code=404,
        )

    # Update access count
    link.access_count += 1
    link.last_accessed_at = datetime.utcnow()
    await session.commit()

    # Get statement data from in-memory store
    data = _statement_store.get(link.account_id, {})

    html = generate_bank_portal_page(
        bank_name=link.bank_name or data.get("bankName", "Your Bank"),
        account_holder=link.account_holder or data.get("accountHolder", "Account Holder"),
        account_number=link.account_id,
        period=data.get("period", "Monthly Statement"),
        branch=data.get("branch", "Main Branch"),
        ifsc=data.get("ifsc", "BANK0001234"),
        address=data.get("address", "Customer Address"),
        opening_balance=data.get("openingBalance", "25000.00"),
        closing_balance=data.get("closingBalance", "25000.00"),
        total_debits=data.get("totalDebits", "0.00"),
        total_credits=data.get("totalCredits", "0.00"),
        transactions=data.get("transactions", []),
        password=link.account_id[-4:] if len(link.account_id) >= 4 else link.account_id,
        verification_id=verification_id,
    )
    return HTMLResponse(content=html)


@router.post("/email-template")
async def generate_email_template(req: BGVEmailTemplateRequest):
    """Generate an HTML email template for BGV confirmation."""
    base_url = "http://localhost:8080"
    view_url = f"{base_url}/api/bgv/view/{req.verificationId}" if req.verificationId else ""
    password = req.accountId[-4:] if len(req.accountId) >= 4 else req.accountId

    html_content = generate_email_html(
        bank_name=req.bankName,
        account_holder=req.accountHolder,
        account_id=req.accountId,
        view_url=view_url,
        password=password,
    )

    return {
        "status": "ok",
        "subject": f"Your {req.bankName} Account Statement - Verification Required",
        "toEmail": req.toEmail,
        "htmlContent": html_content,
        "textContent": f"Dear Account Holder, your {req.bankName} statement is ready.",
        "fromEmail": f"{req.bankName} Statement Service",
    }


@router.get("/links")
async def list_verification_links(session: AsyncSession = Depends(get_session)):
    """List all verification links."""
    result = await session.execute(
        select(VerificationLink).order_by(VerificationLink.created_at.desc())
    )
    links = result.scalars().all()

    output = []
    base_url = "http://localhost:8080"
    for link in links:
        output.append({
            "verificationId": link.verification_id,
            "accountId": link.account_id,
            "bankName": link.bank_name or "",
            "accountHolder": link.account_holder or "",
            "status": link.status or "active",
            "accessCount": link.access_count or 0,
            "createdAt": link.created_at.isoformat() if link.created_at else "",
            "lastAccessedAt": link.last_accessed_at.isoformat() if link.last_accessed_at else "-",
            "viewUrl": f"{base_url}/api/bgv/view/{link.verification_id}",
            "password": link.account_id[-4:] if len(link.account_id) >= 4 else link.account_id,
        })
    return output


@router.get("/stats")
async def get_bgv_stats(session: AsyncSession = Depends(get_session)):
    """Get BGV dashboard stats."""
    result = await session.execute(select(VerificationLink))
    links = result.scalars().all()

    total = len(links)
    active = sum(1 for l in links if l.status == "active")
    total_accesses = sum(l.access_count or 0 for l in links)

    return {
        "totalLinks": total,
        "activeLinks": active,
        "totalAccesses": total_accesses,
    }
