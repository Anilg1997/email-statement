"""API endpoints for Inbound BGV Email Auto-Responder."""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.schemas.inbound_email import (
    InboundEmailConfigSchema,
    InboundEmailConfigResponse,
    InboundEmailLogEntry,
    InboundEmailLogResponse,
    CheckInboxResponse,
)
from app.models.inbound_email import InboundEmailConfig, InboundEmailLog
from app.database import get_session
from app.services.inbound_email_service import (
    InboundEmailProcessor,
    get_active_processor,
    set_active_processor,
)
from app import config_store

router = APIRouter(prefix="/bgv/inbound", tags=["bgv-inbound"])


@router.post("/config", response_model=CheckInboxResponse)
async def save_inbound_config(
    config: InboundEmailConfigSchema,
    session: AsyncSession = Depends(get_session),
):
    """Save the inbound BGV email IMAP configuration."""
    # Get existing config or create new
    result = await session.execute(
        select(InboundEmailConfig).where(InboundEmailConfig.is_active == True)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.imap_host = config.imapHost
        existing.imap_port = config.imapPort
        existing.imap_username = config.imapUsername
        existing.imap_password = config.imapPassword
        existing.use_ssl = config.useSsl
        existing.company_email = config.companyEmail
        existing.bgv_sender_filter = config.bgvSenderFilter
        existing.reply_enabled = config.replyEnabled
        existing.reply_from_name = config.replyFromName
        existing.include_pdf_attachment = config.includePdfAttachment
        existing.include_verification_link = config.includeVerificationLink
        existing.updated_at = datetime.utcnow()
    else:
        db_config = InboundEmailConfig(
            imap_host=config.imapHost,
            imap_port=config.imapPort,
            imap_username=config.imapUsername,
            imap_password=config.imapPassword,
            use_ssl=config.useSsl,
            company_email=config.companyEmail,
            bgv_sender_filter=config.bgvSenderFilter,
            reply_enabled=config.replyEnabled,
            reply_from_name=config.replyFromName,
            include_pdf_attachment=config.includePdfAttachment,
            include_verification_link=config.includeVerificationLink,
        )
        session.add(db_config)

    await session.commit()

    # Create/update the active processor
    if config_store.active_smtp_config and config_store.active_smtp_config.is_configured():
        processor = InboundEmailProcessor(
            imap_host=config.imapHost,
            imap_port=config.imapPort,
            imap_username=config.imapUsername,
            imap_password=config.imapPassword,
            use_ssl=config.useSsl,
            company_email=config.companyEmail,
            bgv_sender_filter=config.bgvSenderFilter,
            reply_from_name=config.replyFromName,
            include_pdf_attachment=config.includePdfAttachment,
            include_verification_link=config.includeVerificationLink,
        )
        processor.set_smtp_config(config_store.active_smtp_config)
        set_active_processor(processor)
    else:
        set_active_processor(None)
        return CheckInboxResponse(
            status="warning",
            details=[
                {"action": "config_saved", "warning": "Config saved but SMTP not configured. Set up email SMTP settings first."}
            ],
        )

    return CheckInboxResponse(
        status="ok",
        details=[
            {"action": "config_saved", "message": f"Inbound email configured for {config.companyEmail} via {config.imapHost}"}
        ],
    )


@router.get("/config", response_model=InboundEmailConfigResponse)
async def get_inbound_config(session: AsyncSession = Depends(get_session)):
    """Get the current inbound email configuration status."""
    result = await session.execute(
        select(InboundEmailConfig).where(InboundEmailConfig.is_active == True)
    )
    config = result.scalar_one_or_none()

    if not config:
        return InboundEmailConfigResponse(configured=False)

    return InboundEmailConfigResponse(
        configured=True,
        imapHost=config.imap_host or "",
        imapPort=config.imap_port or 993,
        imapUsername=config.imap_username or "",
        companyEmail=config.company_email or "",
        bgvSenderFilter=config.bgv_sender_filter or "",
        replyEnabled=config.reply_enabled if config.reply_enabled is not None else True,
        replyFromName=config.reply_from_name or "BGV Verification Service",
        includePdfAttachment=config.include_pdf_attachment if config.include_pdf_attachment is not None else True,
        includeVerificationLink=config.include_verification_link if config.include_verification_link is not None else True,
    )


@router.post("/check", response_model=CheckInboxResponse)
async def check_inbox(session: AsyncSession = Depends(get_session)):
    """Manually check the inbox for BGV emails and auto-reply."""
    processor = get_active_processor()
    if not processor:
        # Try to load from DB
        result = await session.execute(
            select(InboundEmailConfig).where(InboundEmailConfig.is_active == True)
        )
        db_config = result.scalar_one_or_none()
        if not db_config:
            return CheckInboxResponse(
                status="error",
                details=[{"error": "Inbound email not configured. Set up IMAP settings first."}],
            )

        if not config_store.active_smtp_config or not config_store.active_smtp_config.is_configured():
            return CheckInboxResponse(
                status="error",
                details=[{"error": "SMTP not configured. Set up email SMTP settings first."}],
            )

        processor = InboundEmailProcessor(
            imap_host=db_config.imap_host,
            imap_port=db_config.imap_port,
            imap_username=db_config.imap_username,
            imap_password=db_config.imap_password,
            use_ssl=db_config.use_ssl,
            company_email=db_config.company_email,
            bgv_sender_filter=db_config.bgv_sender_filter or "",
            reply_from_name=db_config.reply_from_name or "BGV Verification Service",
            include_pdf_attachment=db_config.include_pdf_attachment if db_config.include_pdf_attachment is not None else True,
            include_verification_link=db_config.include_verification_link if db_config.include_verification_link is not None else True,
        )
        processor.set_smtp_config(config_store.active_smtp_config)
        set_active_processor(processor)

    # Run the inbox check
    results = await processor.check_inbox(db_session=session)

    return CheckInboxResponse(
        status=results.get("status", "ok"),
        totalEmails=results.get("totalEmails", 0),
        bgvMatched=results.get("bgvMatched", 0),
        repliesSent=results.get("repliesSent", 0),
        skipped=results.get("skipped", 0),
        failed=results.get("failed", 0),
        details=results.get("details", []),
    )


@router.get("/logs", response_model=InboundEmailLogResponse)
async def get_inbound_logs(
    limit: int = 50,
    skip: int = 0,
    session: AsyncSession = Depends(get_session),
):
    """Get the log of processed inbound BGV emails."""
    # Get total count
    count_result = await session.execute(
        select(func.count(InboundEmailLog.id))
    )
    total = count_result.scalar() or 0

    # Get logs
    result = await session.execute(
        select(InboundEmailLog)
        .order_by(desc(InboundEmailLog.processed_at))
        .offset(skip)
        .limit(limit)
    )
    logs = result.scalars().all()

    # Compute stats
    sent_result = await session.execute(
        select(func.count(InboundEmailLog.id))
        .where(InboundEmailLog.reply_sent == True)
    )
    total_sent = sent_result.scalar() or 0

    failed_result = await session.execute(
        select(func.count(InboundEmailLog.id))
        .where(InboundEmailLog.bgv_status == "failed")
    )
    total_failed = failed_result.scalar() or 0

    entries = []
    for log in logs:
        entry = InboundEmailLogEntry(
            id=log.id,
            emailUid=log.email_uid,
            sender=log.sender,
            subject=log.subject,
            bodyPreview=(log.body_preview or "")[:200],
            receivedAt=log.received_at.isoformat() if log.received_at else None,
            detectedKeywords=log.detected_keywords or [],
            extractedAccountId=log.extracted_account_id,
            bgvStatus=log.bgv_status or "pending",
            replySent=log.reply_sent or False,
            replySubject=log.reply_subject,
            replyVerificationId=log.reply_verification_id,
            replySentAt=log.reply_sent_at.isoformat() if log.reply_sent_at else None,
            replyError=log.reply_error,
            processedAt=log.processed_at.isoformat() if log.processed_at else None,
        )
        entries.append(entry)

    return InboundEmailLogResponse(
        logs=entries,
        total=total,
        stats={
            "totalEmails": total,
            "repliesSent": total_sent,
            "repliesFailed": total_failed,
            "processed": total - total_failed,
        },
    )
