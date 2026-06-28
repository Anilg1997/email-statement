from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime
from app.database import Base


class EmailConfig(Base):
    __tablename__ = "email_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    host = Column(String(255), nullable=False)
    port = Column(Integer, default=587)
    username = Column(String(255), nullable=False)
    password = Column(Text, nullable=False)
    use_ssl = Column(Boolean, default=True)
    from_name = Column(String(100), default="Bank Statement Service")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
