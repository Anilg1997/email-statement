from fastapi import APIRouter, HTTPException, Depends
from app.schemas.email import EmailConfigSchema, EmailSendRequest
from app.services.email_service import EmailConfig as EmailConfigObj, send_statement_email
from app.services.pdf_encryptor import encrypt_pdf
from app.database import get_session
from app.models.upload import UploadedPdf
from app.models.email_config import EmailConfig
from app import config_store
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(tags=["email"])

# In-memory SMTP config
_current_config: EmailConfigObj | None = None


@router.post("/email/config")
async def save_email_config(config: EmailConfigSchema, session: AsyncSession = Depends(get_session)):
    """Save email SMTP configuration."""
    global _current_config

    # Save to DB
    result = await session.execute(select(EmailConfig).where(EmailConfig.is_active == True))
    existing = result.scalar_one_or_none()
    if existing:
        existing.host = config.host
        existing.port = config.port
        existing.username = config.username
        existing.password = config.password
        existing.use_ssl = config.useSsl
        existing.from_name = config.fromName
    else:
        db_config = EmailConfig(
            host=config.host,
            port=config.port,
            username=config.username,
            password=config.password,
            use_ssl=config.useSsl,
            from_name=config.fromName,
        )
        session.add(db_config)
    await session.commit()

    # Update in-memory config and shared config store
    _current_config = EmailConfigObj(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        use_ssl=config.useSsl,
        from_name=config.fromName,
    )
    # Sync to shared config store for other modules to use
    config_store.active_smtp_config = _current_config
    return {"status": "ok", "message": "Email configured successfully"}


@router.get("/email/config")
async def get_email_config():
    """Get current email configuration status."""
    global _current_config
    if _current_config:
        return {
            "configured": True,
            "host": _current_config.host,
            "port": _current_config.port,
            "username": _current_config.username,
            "fromName": _current_config.from_name,
        }
    return {"configured": False, "host": "", "port": 587, "username": "", "fromName": ""}


@router.post("/email/send")
async def send_email(req: EmailSendRequest, session: AsyncSession = Depends(get_session)):
    """Send the uploaded PDF statement via email."""
    global _current_config

    if not _current_config or not _current_config.is_configured():
        # Try loading from DB
        result = await session.execute(select(EmailConfig).where(EmailConfig.is_active == True))
        db_config = result.scalar_one_or_none()
        if db_config:
            _current_config = EmailConfigObj(
                host=db_config.host,
                port=db_config.port,
                username=db_config.username,
                password=db_config.password,
                use_ssl=db_config.use_ssl,
                from_name=db_config.from_name or "Bank Statement Service",
            )
        else:
            return {"status": "error", "message": "Email is not configured. Please set SMTP settings first."}

    if not req.toEmail:
        return {"status": "error", "message": "toEmail is required"}
    if not req.accountId:
        return {"status": "error", "message": "accountId is required"}

    # Look up the uploaded PDF
    result = await session.execute(
        select(UploadedPdf).where(UploadedPdf.account_id == req.accountId)
    )
    uploaded = result.scalar_one_or_none()

    if not uploaded:
        return {
            "status": "error",
            "message": f"No uploaded PDF found for account {req.accountId}. Please upload a PDF first."
        }

    pdf_bytes = uploaded.pdf_data
    password = req.accountId[-4:] if len(req.accountId) >= 4 else req.accountId
    
    # Try to encrypt the PDF, fall back to original if encryption fails
    try:
        encrypted_pdf = encrypt_pdf(pdf_bytes, password)
    except Exception:
        encrypted_pdf = pdf_bytes

    result = await send_statement_email(
        config=_current_config,
        to_email=req.toEmail,
        bank_name=req.bankName,
        account_id=req.accountId,
        pdf_bytes=encrypted_pdf,
    )
    return result
