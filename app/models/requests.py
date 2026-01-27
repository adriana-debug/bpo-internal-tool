from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from app.core.database import Base
from datetime import datetime

class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
