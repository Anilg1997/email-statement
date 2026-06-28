from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import Response
from app.database import get_session
from app.models.upload import UploadedPdf
from app.services.pdf_encryptor import encrypt_pdf
from app.services.email_service import send_statement_email, EmailConfig as SmtpConfig
from app.services.access_tracker import tracker
from app import config_store
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends

router = APIRouter(tags=["upload"])


@router.post("/upload")
async def upload_pdf(accountId: str = Form(...), file: UploadFile = File(...),
                     session: AsyncSession = Depends(get_session)):
    """Upload an edited PDF statement for a specific account."""
    try:
        pdf_bytes = await file.read()

        # Upsert: remove existing then add
        existing = await session.execute(
            select(UploadedPdf).where(UploadedPdf.account_id == accountId)
        )
        existing_pdf = existing.scalar_one_or_none()
        if existing_pdf:
            await session.delete(existing_pdf)

        new_pdf = UploadedPdf(
            account_id=accountId,
            file_name=file.filename or "uploaded.pdf",
            file_size=len(pdf_bytes),
            pdf_data=pdf_bytes,
        )
        session.add(new_pdf)
        await session.commit()

        return {
            "status": "ok",
            "message": f"Uploaded {file.filename} for account {accountId}",
            "password": accountId[-4:] if len(accountId) >= 4 else accountId,
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload-and-send")
async def upload_and_send(
    accountId: str = Form(...),
    file: UploadFile = File(...),
    toEmail: str = Form(None),
    bankName: str = Form(None),
    accountHolder: str = Form(None),
    sendEmail: bool = Form(False),
    session: AsyncSession = Depends(get_session),
):
    """Upload a PDF statement and optionally send it directly via email.
    
    If sendEmail is true and toEmail/bankName are provided, the PDF
    is encrypted and emailed immediately after upload.
    """
    try:
        pdf_bytes = await file.read()

        # Upsert: remove existing then add
        existing = await session.execute(
            select(UploadedPdf).where(UploadedPdf.account_id == accountId)
        )
        existing_pdf = existing.scalar_one_or_none()
        if existing_pdf:
            await session.delete(existing_pdf)

        new_pdf = UploadedPdf(
            account_id=accountId,
            file_name=file.filename or "uploaded.pdf",
            file_size=len(pdf_bytes),
            pdf_data=pdf_bytes,
        )
        session.add(new_pdf)
        await session.commit()

        password = accountId[-4:] if len(accountId) >= 4 else accountId
        response = {
            "status": "ok",
            "message": f"Uploaded {file.filename} for account {accountId}",
            "password": password,
        }

        # If email sending requested, send the email
        if sendEmail and toEmail and bankName:
            smtp_config = config_store.active_smtp_config
            if not smtp_config or not smtp_config.is_configured():
                # Try to load from DB
                from app.models.email_config import EmailConfig
                db_result = await session.execute(
                    select(EmailConfig).where(EmailConfig.is_active == True)
                )
                db_config = db_result.scalar_one_or_none()
                if db_config:
                    smtp_config = SmtpConfig(
                        host=db_config.host,
                        port=db_config.port,
                        username=db_config.username,
                        password=db_config.password,
                        use_ssl=db_config.use_ssl,
                        from_name=db_config.from_name or bank_name,
                    )
                    config_store.active_smtp_config = smtp_config

            if smtp_config and smtp_config.is_configured():
                holder_name = accountHolder or "Account Holder"
                encrypted_pdf = encrypt_pdf(pdf_bytes, password)
                email_result = await send_statement_email(
                    config=smtp_config,
                    to_email=toEmail,
                    bank_name=bankName,
                    account_id=accountId,
                    pdf_bytes=encrypted_pdf,
                )
                response["emailResult"] = email_result
                if email_result.get("status") == "ok":
                    response["message"] += f" | Email sent to {toEmail}"
                else:
                    response["message"] += f" | Email failed: {email_result.get('message', 'unknown error')}"
            else:
                response["message"] += " | SMTP not configured. Please set up email settings first."

        return response
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/replace")
async def replace_endpoint(accountId: str, request: Request, session: AsyncSession = Depends(get_session)):
    """Serve the uploaded PDF for the given account ID, encrypted with password."""
    if not accountId or not accountId.strip():
        raise HTTPException(status_code=400, detail="accountId is required")

    # Track access
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("User-Agent", "")
    referer = request.headers.get("Referer", "")
    source = referer if referer else "direct"
    tracker.log_access(accountId, ip, ua, source)

    # Find the uploaded PDF
    result = await session.execute(
        select(UploadedPdf).where(UploadedPdf.account_id == accountId)
    )
    uploaded = result.scalar_one_or_none()

    if not uploaded:
        raise HTTPException(
            status_code=404,
            detail=f"No uploaded PDF found for account {accountId}. Please upload a PDF first."
        )

    pdf_bytes = uploaded.pdf_data
    password = accountId[-4:] if len(accountId) >= 4 else accountId
    encrypted = encrypt_pdf(pdf_bytes, password)

    return Response(
        content=encrypted,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'inline; filename="statement.pdf"',
            "Content-Length": str(len(encrypted)),
        }
    )


@router.get("/list")
async def list_uploads(session: AsyncSession = Depends(get_session)):
    """List all uploaded PDFs."""
    result = []

    # Get uploaded PDFs
    pdf_result = await session.execute(select(UploadedPdf).order_by(UploadedPdf.created_at.desc()))
    uploaded_pdfs = pdf_result.scalars().all()

    for pdf in uploaded_pdfs:
        result.append({
            "accountId": pdf.account_id,
            "file": f"{pdf.file_name} ({pdf.file_size} bytes)",
            "password": pdf.account_id[-4:] if len(pdf.account_id) >= 4 else pdf.account_id,
        })

    return result
