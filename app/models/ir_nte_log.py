from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class IRNTELog(Base):
    """Incident Report / Notice to Explain Log"""
    __tablename__ = "ir_nte_logs"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String(50), unique=True, index=True)  # IR-2026-0001 or NTE-2026-0001

    # Employee info
    employee_id = Column(Integer, ForeignKey('users.id'), index=True)

    # Document details
    doc_type = Column(String(20), index=True)  # IR, NTE
    filed_date = Column(Date, index=True)
    complaint_violation = Column(Text)  # Description of complaint or violation
    received_date = Column(Date, nullable=True)  # Date employee received the document
    nte_date = Column(Date, nullable=True)  # NTE response deadline

    # Response tracking
    has_explanation = Column(Boolean, default=False)  # Did employee submit explanation?
    explanation_date = Column(Date, nullable=True)
    explanation_summary = Column(Text, nullable=True)

    # Attachments
    attachment_path = Column(String(500), nullable=True)  # Evidence/supporting docs
    nte_form_path = Column(String(500), nullable=True)  # Original NTE/complaint form

    # Status and resolution
    status = Column(String(50), default="Open", index=True)  # Open, Pending Response, Under Review, Resolved, Escalated, Closed
    resolution = Column(String(100), nullable=True)  # Warning, Suspension, Termination, Dismissed, etc.
    resolution_date = Column(Date, nullable=True)
    remarks = Column(Text, nullable=True)

    # Audit fields
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship("User", foreign_keys=[employee_id], backref="ir_nte_logs")
    creator = relationship("User", foreign_keys=[created_by])
