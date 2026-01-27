from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PayDispute(Base):
    __tablename__ = "pay_disputes"

    id = Column(Integer, primary_key=True, index=True)
    ticket_no = Column(String(50), unique=True, index=True)  # PAY-2026-0001

    # Employee info (linked to user)
    employee_id = Column(Integer, ForeignKey('users.id'), index=True)

    # Dispute details
    dispute_type = Column(String(100), index=True)  # Overtime, Deduction, Bonus, Allowance, Tax, Others
    pay_period = Column(String(50))  # "January 2026", "Dec 15-31, 2025"
    disputed_amount = Column(Float, nullable=True)  # Amount in dispute

    # Description and evidence
    subject = Column(String(255))
    description = Column(Text)
    supporting_docs = Column(String(500), nullable=True)  # File paths or references

    # Status tracking
    status = Column(String(50), default="Open", index=True)  # Open, Under Review, Pending Payroll, Resolved, Rejected, Escalated
    priority = Column(String(20), default="Medium")  # Low, Medium, High, Urgent

    # Assignment
    assigned_to = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Resolution
    resolution_notes = Column(Text, nullable=True)
    resolution_amount = Column(Float, nullable=True)  # Adjusted amount if any
    resolved_date = Column(Date, nullable=True)

    # Audit fields
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship("User", foreign_keys=[employee_id], backref="pay_disputes")
    assignee = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])


class PayDisputeComment(Base):
    """Comments/notes on pay disputes for tracking communication"""
    __tablename__ = "pay_dispute_comments"

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(Integer, ForeignKey('pay_disputes.id', ondelete='CASCADE'), index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    comment = Column(Text)
    is_internal = Column(Boolean, default=False)  # Internal notes vs visible to employee
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dispute = relationship("PayDispute", backref="comments")
    user = relationship("User")
