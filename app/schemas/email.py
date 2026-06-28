from pydantic import BaseModel
from typing import Optional


class EmailConfigSchema(BaseModel):
    host: str = "smtp.gmail.com"
    port: int = 587
    username: str = ""
    password: str = ""
    useSsl: bool = True
    fromName: str = "Bank Statement Service"


class EmailConfigResponse(BaseModel):
    configured: bool
    host: str = ""
    port: int = 587
    username: str = ""
    fromName: str = ""


class EmailSendRequest(BaseModel):
    toEmail: str
    accountId: str
    bankName: str = "Your Bank"
    accountHolder: str = "Account Holder"


class EmailSendResponse(BaseModel):
    status: str
    message: str
    to: Optional[str] = None
    subject: Optional[str] = None
    attachment: Optional[str] = None


class AccessLogEntry(BaseModel):
    id: str
    accountId: str
    ipAddress: str
    source: str
    timestamp: str
    userAgent: str


class AccessLogResponse(BaseModel):
    logs: list[AccessLogEntry]
    stats: dict
