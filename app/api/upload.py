from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import Response
from app.database import get_session
from app.models.upload import UploadedPdf
from app.services.pdf_encryptor import encrypt_pdf
from app.services.access_tracker import tracker
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
