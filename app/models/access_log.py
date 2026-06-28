from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.database import Base


class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(12), unique=True)
    account_id = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    source = Column(String(100))
    accessed_at = Column(DateTime, default=datetime.utcnow)
