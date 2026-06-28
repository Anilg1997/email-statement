from pydantic import BaseModel
from typing import Optional


class BGVGenerateRequest(BaseModel):
    accountId: str
    bankName: str = "Your Bank"
    accountHolder: str = "Account Holder"
    mode: str = "portal"


class BGVGenerateResponse(BaseModel):
    status: str
    verificationId: str
    token: str
    viewUrl: str
    createdAt: str
    password: str
    mode: str


class BGVEmailTemplateRequest(BaseModel):
    accountId: str
    bankName: str = "Your Bank"
    accountHolder: str = "Account Holder"
    toEmail: str
    verificationId: str = ""


class BGVEmailTemplateResponse(BaseModel):
    status: str
    subject: str
    toEmail: str
    htmlContent: str
    textContent: str
    fromEmail: str


class BGVLinkItem(BaseModel):
    verificationId: str
    accountId: str
    bankName: str
    accountHolder: str
    status: str
    accessCount: int
    lastAccessedAt: str
    createdAt: str
    viewUrl: str
    password: str
