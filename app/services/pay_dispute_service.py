from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from app.models.user import User
from app.models.pay_dispute import PayDispute, PayDisputeComment
from app.schemas.pay_dispute import PayDisputeCreate, PayDisputeUpdate, PayDisputeFilter, PayDisputeCommentCreate


def generate_ticket_number(db: Session) -> str:
    """Generate unique ticket number: PAY-YYYY-NNNN"""
    year = datetime.now().year
    prefix = f"PAY-{year}-"

    # Get the highest ticket number for this year
    latest = db.query(PayDispute).filter(
        PayDispute.ticket_no.like(f"{prefix}%")
    ).order_by(PayDispute.id.desc()).first()

    if latest:
        try:
            last_num = int(latest.ticket_no.split("-")[-1])
            new_num = last_num + 1
        except ValueError:
            new_num = 1
    else:
        new_num = 1

    return f"{prefix}{new_num:04d}"


def get_pay_disputes(
    db: Session,
    filters: PayDisputeFilter
) -> Dict[str, Any]:
    """Get pay disputes with filtering and pagination"""
    query = db.query(PayDispute).join(User, PayDispute.employee_id == User.id)

    # Apply search filter
    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.employee_no.ilike(search_term),
                PayDispute.ticket_no.ilike(search_term),
                PayDispute.subject.ilike(search_term)
            )
        )

    # Apply status filter
    if filters.status:
        query = query.filter(PayDispute.status == filters.status)

    # Apply dispute type filter
    if filters.dispute_type:
        query = query.filter(PayDispute.dispute_type == filters.dispute_type)

    # Apply priority filter
    if filters.priority:
        query = query.filter(PayDispute.priority == filters.priority)

    # Apply campaign filter
    if filters.campaign:
        query = query.filter(User.campaign == filters.campaign)

    # Apply assigned_to filter
    if filters.assigned_to:
        query = query.filter(PayDispute.assigned_to == filters.assigned_to)

    # Apply date range filter
    if filters.date_from:
        query = query.filter(func.date(PayDispute.created_at) >= filters.date_from)
    if filters.date_to:
        query = query.filter(func.date(PayDispute.created_at) <= filters.date_to)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (filters.page - 1) * filters.limit
    disputes = query.order_by(PayDispute.created_at.desc()).offset(offset).limit(filters.limit).all()

    # Format records with user info
    formatted_disputes = []
    for dispute in disputes:
        formatted_disputes.append({
            "id": dispute.id,
            "ticket_no": dispute.ticket_no,
            "employee_id": dispute.employee_id,
            "employee_name": dispute.employee.full_name if dispute.employee else None,
            "employee_no": dispute.employee.employee_no if dispute.employee else None,
            "campaign": dispute.employee.campaign if dispute.employee else None,
            "dispute_type": dispute.dispute_type,
            "pay_period": dispute.pay_period,
            "disputed_amount": dispute.disputed_amount,
            "subject": dispute.subject,
            "description": dispute.description,
            "supporting_docs": dispute.supporting_docs,
            "status": dispute.status,
            "priority": dispute.priority,
            "assigned_to": dispute.assigned_to,
            "assignee_name": dispute.assignee.full_name if dispute.assignee else None,
            "resolution_notes": dispute.resolution_notes,
            "resolution_amount": dispute.resolution_amount,
            "resolved_date": dispute.resolved_date.isoformat() if dispute.resolved_date else None,
            "created_by": dispute.created_by,
            "creator_name": dispute.creator.full_name if dispute.creator else None,
            "created_at": dispute.created_at.isoformat() if dispute.created_at else None,
            "updated_at": dispute.updated_at.isoformat() if dispute.updated_at else None
        })

    return {
        "disputes": formatted_disputes,
        "total": total,
        "page": filters.page,
        "limit": filters.limit,
        "pages": (total + filters.limit - 1) // filters.limit
    }


def get_pay_dispute_by_id(db: Session, dispute_id: int) -> Optional[PayDispute]:
    """Get single pay dispute by ID"""
    return db.query(PayDispute).filter(PayDispute.id == dispute_id).first()


def get_pay_dispute_by_ticket(db: Session, ticket_no: str) -> Optional[PayDispute]:
    """Get single pay dispute by ticket number"""
    return db.query(PayDispute).filter(PayDispute.ticket_no == ticket_no).first()


def create_pay_dispute(db: Session, dispute_data: PayDisputeCreate, created_by: int) -> PayDispute:
    """Create a new pay dispute"""
    dispute = PayDispute(
        ticket_no=generate_ticket_number(db),
        employee_id=dispute_data.employee_id,
        dispute_type=dispute_data.dispute_type,
        pay_period=dispute_data.pay_period,
        disputed_amount=dispute_data.disputed_amount,
        subject=dispute_data.subject,
        description=dispute_data.description,
        supporting_docs=dispute_data.supporting_docs,
        priority=dispute_data.priority,
        status="Open",
        created_by=created_by
    )
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    return dispute


def update_pay_dispute(db: Session, dispute_id: int, dispute_data: PayDisputeUpdate) -> Optional[PayDispute]:
    """Update an existing pay dispute"""
    dispute = get_pay_dispute_by_id(db, dispute_id)
    if not dispute:
        return None

    update_data = dispute_data.model_dump(exclude_unset=True)

    # If status changes to Resolved, set resolved_date
    if update_data.get("status") == "Resolved" and not dispute.resolved_date:
        update_data["resolved_date"] = date.today()

    for field, value in update_data.items():
        setattr(dispute, field, value)

    db.commit()
    db.refresh(dispute)
    return dispute


def delete_pay_dispute(db: Session, dispute_id: int) -> bool:
    """Delete a pay dispute"""
    dispute = get_pay_dispute_by_id(db, dispute_id)
    if not dispute:
        return False

    db.delete(dispute)
    db.commit()
    return True


def get_pay_dispute_statistics(db: Session, date_from: Optional[date] = None, date_to: Optional[date] = None) -> Dict[str, Any]:
    """Get pay dispute statistics"""
    query = db.query(PayDispute)

    if date_from:
        query = query.filter(func.date(PayDispute.created_at) >= date_from)
    if date_to:
        query = query.filter(func.date(PayDispute.created_at) <= date_to)

    disputes = query.all()
    total = len(disputes)

    open_count = sum(1 for d in disputes if d.status == "Open")
    under_review_count = sum(1 for d in disputes if d.status == "Under Review")
    pending_payroll_count = sum(1 for d in disputes if d.status == "Pending Payroll")
    resolved_count = sum(1 for d in disputes if d.status == "Resolved")
    rejected_count = sum(1 for d in disputes if d.status == "Rejected")
    escalated_count = sum(1 for d in disputes if d.status == "Escalated")

    total_disputed = sum(d.disputed_amount or 0 for d in disputes)
    total_resolved = sum(d.resolution_amount or 0 for d in disputes if d.status == "Resolved")

    return {
        "total_disputes": total,
        "open_count": open_count,
        "under_review_count": under_review_count,
        "pending_payroll_count": pending_payroll_count,
        "resolved_count": resolved_count,
        "rejected_count": rejected_count,
        "escalated_count": escalated_count,
        "total_disputed_amount": round(total_disputed, 2),
        "total_resolved_amount": round(total_resolved, 2)
    }


def get_filter_options(db: Session) -> Dict[str, List[str]]:
    """Get unique values for filter dropdowns"""
    # Get unique campaigns from employees with disputes
    campaigns = db.query(User.campaign).join(
        PayDispute, PayDispute.employee_id == User.id
    ).filter(User.campaign.isnot(None)).distinct().all()

    # Get unique dispute types
    types = db.query(PayDispute.dispute_type).distinct().all()

    # Get unique statuses
    statuses = db.query(PayDispute.status).distinct().all()

    # Get unique priorities
    priorities = db.query(PayDispute.priority).distinct().all()

    # Get assignees (users who have been assigned disputes)
    assignees = db.query(User.id, User.full_name).join(
        PayDispute, PayDispute.assigned_to == User.id
    ).distinct().all()

    return {
        "campaigns": sorted([c[0] for c in campaigns if c[0]]),
        "dispute_types": sorted([t[0] for t in types if t[0]]),
        "statuses": sorted([s[0] for s in statuses if s[0]]),
        "priorities": ["Low", "Medium", "High", "Urgent"],
        "assignees": [{"id": a[0], "name": a[1]} for a in assignees]
    }


# Comment functions
def add_comment(db: Session, dispute_id: int, user_id: int, comment_data: PayDisputeCommentCreate) -> PayDisputeComment:
    """Add a comment to a pay dispute"""
    comment = PayDisputeComment(
        dispute_id=dispute_id,
        user_id=user_id,
        comment=comment_data.comment,
        is_internal=comment_data.is_internal
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comments(db: Session, dispute_id: int, include_internal: bool = True) -> List[Dict[str, Any]]:
    """Get comments for a pay dispute"""
    query = db.query(PayDisputeComment).filter(PayDisputeComment.dispute_id == dispute_id)

    if not include_internal:
        query = query.filter(PayDisputeComment.is_internal == False)

    comments = query.order_by(PayDisputeComment.created_at.desc()).all()

    return [{
        "id": c.id,
        "dispute_id": c.dispute_id,
        "user_id": c.user_id,
        "user_name": c.user.full_name if c.user else None,
        "comment": c.comment,
        "is_internal": c.is_internal,
        "created_at": c.created_at.isoformat() if c.created_at else None
    } for c in comments]
