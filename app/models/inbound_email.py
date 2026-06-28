"""Database models for Inbound BGV Email Auto-Responder."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, JSON
from app.database import Base


class InboundEmailConfig(Base):
    """IMAP configuration for the company BGV email inbox."""

    __tablename__ = "inbound_email_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # IMAP settings
    imap_host = Column(String(255), nullable=False)
    imap_port = Column(Integer, default=993)
    imap_username = Column(String(255), nullable=False)
    imap_password = Column(Text, nullable=False)
    use_ssl = Column(Boolean, default=True)
    # Company email address (e.g. hhrrr@borngroup.com)
    company_email = Column(String(255), nullable=False)
    # BGV sender filter: if set, only process emails from this address/domain
    bgv_sender_filter = Column(String(255), nullable=True)
    # Auto-reply settings
    reply_enabled = Column(Boolean, default=True)
    reply_from_name = Column(String(100), default="BGV Verification Service")
    # Whether to include PDF attachment in reply
    include_pdf_attachment = Column(Boolean, default=True)
    # Whether to include verification link in reply
    include_verification_link = Column(Boolean, default=True)
    # Active flag
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InboundEmailLog(Base):
    """Log of processed inbound BGV emails and their auto-replies."""

    __tablename__ = "inbound_email_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Original email details
    email_uid = Column(String(255), unique=True, nullable=False)
    sender = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body_preview = Column(Text, nullable=True)
    received_at = Column(DateTime, nullable=True)
    # Processing results
    detected_keywords = Column(JSON, nullable=True)
    extracted_account_id = Column(String(50), nullable=True)
    bgv_status = Column(String(50), default="pending")  # pending, processed, skipped, failed
    # Reply details
    reply_sent = Column(Boolean, default=False)
    reply_subject = Column(String(500), nullable=True)
    reply_message = Column(Text, nullable=True)
    reply_verification_id = Column(String(50), nullable=True)
    reply_sent_at = Column(DateTime, nullable=True)
    reply_error = Column(Text, nullable=True)
    # Processing metadata
    processed_at = Column(DateTime, default=datetime.utcnow)
