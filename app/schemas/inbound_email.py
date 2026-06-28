"""Pydantic schemas for Inbound BGV Email Auto-Responder."""

from pydantic import BaseModel
from typing import Optional, Any


class InboundEmailConfigSchema(BaseModel):
    """Schema for configuring the inbound BGV email IMAP settings."""
    imapHost: str = "imap.gmail.com"
    imapPort: int = 993
    imapUsername: str = ""
    imapPassword: str = ""
    useSsl: bool = True
    companyEmail: str = ""
    bgvSenderFilter: str = ""
    replyEnabled: bool = True
    replyFromName: str = "BGV Verification Service"
    includePdfAttachment: bool = True
    includeVerificationLink: bool = True


class InboundEmailConfigResponse(BaseModel):
    """Schema for returning config status."""
    configured: bool = False
    imapHost: str = ""
    imapPort: int = 993
    imapUsername: str = ""
    companyEmail: str = ""
    bgvSenderFilter: str = ""
    replyEnabled: bool = True
    replyFromName: str = ""
    includePdfAttachment: bool = True
    includeVerificationLink: bool = True


class InboundEmailLogEntry(BaseModel):
    """Schema for a single inbound email log entry."""
    id: int
    emailUid: str
    sender: str
    subject: str
    bodyPreview: str = ""
    receivedAt: Optional[str] = None
    detectedKeywords: list[str] = []
    extractedAccountId: Optional[str] = None
    bgvStatus: str = "pending"
    replySent: bool = False
    replySubject: Optional[str] = None
    replyVerificationId: Optional[str] = None
    replySentAt: Optional[str] = None
    replyError: Optional[str] = None
    processedAt: Optional[str] = None


class InboundEmailLogResponse(BaseModel):
    """Schema for listing inbound email logs."""
    logs: list[InboundEmailLogEntry] = []
    total: int = 0
    stats: dict[str, Any] = {}


class CheckInboxResponse(BaseModel):
    """Schema for inbox check result."""
    status: str
    totalEmails: int = 0
    bgvMatched: int = 0
    repliesSent: int = 0
    skipped: int = 0
    failed: int = 0
    details: list[dict] = []
