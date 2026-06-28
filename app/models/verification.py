from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.database import Base


class VerificationLink(Base):
    __tablename__ = "verification_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    verification_id = Column(String(50), unique=True, nullable=False, index=True)
    account_id = Column(String(50), nullable=False)
    bank_name = Column(String(100))
    account_holder = Column(String(200))
    mode = Column(String(20), default="portal")
    status = Column(String(20), default="active")
    access_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, nullable=True)
