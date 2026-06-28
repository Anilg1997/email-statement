from pydantic import BaseModel
from typing import Optional


class UploadResponse(BaseModel):
    status: str
    message: str


class ListItem(BaseModel):
    accountId: str
    file: str


class ImportResponse(BaseModel):
    status: str
    bankName: Optional[str] = None
    accountNumber: Optional[str] = None
    accountHolder: Optional[str] = None
    period: Optional[str] = None
    branch: Optional[str] = None
    ifsc: Optional[str] = None
    address: Optional[str] = None
    openingBalance: Optional[str] = None
    closingBalance: Optional[str] = None
    transactions: list = []
    transactionsCount: int = 0
    extractedText: Optional[str] = None
    textLength: int = 0
    message: Optional[str] = None
    autoPassword: Optional[str] = None
    debug: Optional[dict] = None
