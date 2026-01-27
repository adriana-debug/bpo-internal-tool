from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import date, datetime
from typing import Optional, Dict, Any, List
from app.models.user import User
from app.models.ir_nte_log import IRNTELog
from app.schemas.ir_nte_log import IRNTELogCreate, IRNTELogUpdate, IRNTELogFilter


def generate_doc_id(db: Session, doc_type: str) -> str:
    """Generate unique document ID: IR-YYYY-NNNN or NTE-YYYY-NNNN"""
    year = datetime.now().year
    prefix = f"{doc_type}-{year}-"

    latest = db.query(IRNTELog).filter(
        IRNTELog.doc_id.like(f"{prefix}%")
    ).order_by(IRNTELog.id.desc()).first()

    if latest:
        try:
            last_num = int(latest.doc_id.split("-")[-1])
            new_num = last_num + 1
        except ValueError:
            new_num = 1
    else:
        new_num = 1

    return f"{prefix}{new_num:04d}"


def get_ir_nte_logs(db: Session, filters: IRNTELogFilter) -> Dict[str, Any]:
    """Get IR/NTE logs with filtering and pagination"""
    query = db.query(IRNTELog).join(User, IRNTELog.employee_id == User.id)

    # Search filter
    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.employee_no.ilike(search_term),
                IRNTELog.doc_id.ilike(search_term),
                IRNTELog.complaint_violation.ilike(search_term)
            )
        )

    # Doc type filter
    if filters.doc_type:
        query = query.filter(IRNTELog.doc_type == filters.doc_type)

    # Status filter
    if filters.status:
        query = query.filter(IRNTELog.status == filters.status)

    # Campaign filter
    if filters.campaign:
        query = query.filter(User.campaign == filters.campaign)

    # Filed date range
    if filters.filed_date_from:
        query = query.filter(IRNTELog.filed_date >= filters.filed_date_from)
    if filters.filed_date_to:
        query = query.filter(IRNTELog.filed_date <= filters.filed_date_to)

    # NTE date range
    if filters.nte_date_from:
        query = query.filter(IRNTELog.nte_date >= filters.nte_date_from)
    if filters.nte_date_to:
        query = query.filter(IRNTELog.nte_date <= filters.nte_date_to)

    # Explanation filter
    if filters.has_explanation is not None:
        query = query.filter(IRNTELog.has_explanation == filters.has_explanation)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (filters.page - 1) * filters.limit
    logs = query.order_by(IRNTELog.filed_date.desc()).offset(offset).limit(filters.limit).all()

    # Format records
    formatted_logs = []
    for log in logs:
        formatted_logs.append({
            "id": log.id,
            "doc_id": log.doc_id,
            "doc_type": log.doc_type,
            "employee_id": log.employee_id,
            "employee_name": log.employee.full_name if log.employee else None,
            "employee_no": log.employee.employee_no if log.employee else None,
            "campaign": log.employee.campaign if log.employee else None,
            "filed_date": log.filed_date.isoformat() if log.filed_date else None,
            "complaint_violation": log.complaint_violation,
            "received_date": log.received_date.isoformat() if log.received_date else None,
            "nte_date": log.nte_date.isoformat() if log.nte_date else None,
            "has_explanation": log.has_explanation,
            "explanation_date": log.explanation_date.isoformat() if log.explanation_date else None,
            "explanation_summary": log.explanation_summary,
            "attachment_path": log.attachment_path,
            "nte_form_path": log.nte_form_path,
            "status": log.status,
            "resolution": log.resolution,
            "resolution_date": log.resolution_date.isoformat() if log.resolution_date else None,
            "remarks": log.remarks,
            "created_by": log.created_by,
            "creator_name": log.creator.full_name if log.creator else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "updated_at": log.updated_at.isoformat() if log.updated_at else None
        })

    return {
        "logs": formatted_logs,
        "total": total,
        "page": filters.page,
        "limit": filters.limit,
        "pages": (total + filters.limit - 1) // filters.limit
    }


def get_ir_nte_by_id(db: Session, log_id: int) -> Optional[IRNTELog]:
    """Get single IR/NTE log by ID"""
    return db.query(IRNTELog).filter(IRNTELog.id == log_id).first()


def create_ir_nte_log(db: Session, log_data: IRNTELogCreate, created_by: int) -> IRNTELog:
    """Create a new IR/NTE log"""
    log = IRNTELog(
        doc_id=generate_doc_id(db, log_data.doc_type),
        employee_id=log_data.employee_id,
        doc_type=log_data.doc_type,
        filed_date=log_data.filed_date,
        complaint_violation=log_data.complaint_violation,
        received_date=log_data.received_date,
        nte_date=log_data.nte_date,
        attachment_path=log_data.attachment_path,
        nte_form_path=log_data.nte_form_path,
        remarks=log_data.remarks,
        status="Open",
        created_by=created_by
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def update_ir_nte_log(db: Session, log_id: int, log_data: IRNTELogUpdate) -> Optional[IRNTELog]:
    """Update an existing IR/NTE log"""
    log = get_ir_nte_by_id(db, log_id)
    if not log:
        return None

    update_data = log_data.model_dump(exclude_unset=True)

    # If status changes to Resolved/Closed, set resolution_date
    if update_data.get("status") in ["Resolved", "Closed"] and not log.resolution_date:
        update_data["resolution_date"] = date.today()

    for field, value in update_data.items():
        setattr(log, field, value)

    db.commit()
    db.refresh(log)
    return log


def delete_ir_nte_log(db: Session, log_id: int) -> bool:
    """Delete an IR/NTE log"""
    log = get_ir_nte_by_id(db, log_id)
    if not log:
        return False

    db.delete(log)
    db.commit()
    return True


def get_ir_nte_statistics(db: Session) -> Dict[str, Any]:
    """Get IR/NTE log statistics"""
    logs = db.query(IRNTELog).all()
    total = len(logs)

    open_count = sum(1 for l in logs if l.status == "Open")
    pending_count = sum(1 for l in logs if l.status == "Pending Response")
    under_review_count = sum(1 for l in logs if l.status == "Under Review")
    resolved_count = sum(1 for l in logs if l.status in ["Resolved", "Closed"])
    escalated_count = sum(1 for l in logs if l.status == "Escalated")

    ir_count = sum(1 for l in logs if l.doc_type == "IR")
    nte_count = sum(1 for l in logs if l.doc_type == "NTE")

    return {
        "total_records": total,
        "open_count": open_count,
        "pending_count": pending_count,
        "under_review_count": under_review_count,
        "resolved_count": resolved_count,
        "escalated_count": escalated_count,
        "ir_count": ir_count,
        "nte_count": nte_count
    }


def get_filter_options(db: Session) -> Dict[str, List[str]]:
    """Get unique values for filter dropdowns"""
    campaigns = db.query(User.campaign).join(
        IRNTELog, IRNTELog.employee_id == User.id
    ).filter(User.campaign.isnot(None)).distinct().all()

    statuses = db.query(IRNTELog.status).distinct().all()

    return {
        "campaigns": sorted([c[0] for c in campaigns if c[0]]),
        "statuses": sorted([s[0] for s in statuses if s[0]]),
        "doc_types": ["IR", "NTE"],
        "resolutions": ["Warning", "Written Warning", "Final Warning", "Suspension", "Termination", "Dismissed", "No Action"]
    }
