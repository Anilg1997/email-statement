import uuid
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, LargeBinary, DateTime, Text
from app.database import Base


def generate_uuid() -> str:
    return uuid.uuid4().hex[:12]


class UploadedPdf(Base):
    __tablename__ = "uploaded_pdfs"

    id = Column(String(12), primary_key=True, default=generate_uuid)
    account_id = Column(String(50), unique=True, nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, default=0)
    pdf_data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
