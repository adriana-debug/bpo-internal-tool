from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import date, time, timedelta
from typing import Optional, List, Dict, Any
from app.models.user import User, DailyTimeRecord
from app.schemas.dtr import DTRCreate, DTRUpdate, DTRFilter


def get_dtr_records(
    db: Session,
    filters: DTRFilter
) -> Dict[str, Any]:
    """Get DTR records with filtering and pagination"""
    query = db.query(DailyTimeRecord).join(User)

    # Apply search filter
    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.employee_no.ilike(search_term),
                User.email.ilike(search_term)
            )
        )

    # Apply campaign filter
    if filters.campaign:
        query = query.filter(User.campaign == filters.campaign)

    # Apply date range filter
    if filters.date_from:
        query = query.filter(DailyTimeRecord.date >= filters.date_from)
    if filters.date_to:
        query = query.filter(DailyTimeRecord.date <= filters.date_to)

    # Apply shift filter
    if filters.shift:
        query = query.filter(DailyTimeRecord.scheduled_shift == filters.shift)

    # Apply status filter
    if filters.status:
        query = query.filter(DailyTimeRecord.status == filters.status)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (filters.page - 1) * filters.limit
    records = query.order_by(DailyTimeRecord.date.desc(), User.full_name).offset(offset).limit(filters.limit).all()

    # Format records with user info
    formatted_records = []
    for record in records:
        formatted_records.append({
            "id": record.id,
            "user_id": record.user_id,
            "employee_name": record.user.full_name if record.user else None,
            "employee_no": record.user.employee_no if record.user else None,
            "campaign": record.user.campaign if record.user else None,
            "date": record.date.isoformat() if record.date else None,
            "scheduled_shift": record.scheduled_shift,
            "time_in": record.time_in.strftime("%H:%M") if record.time_in else None,
            "time_out": record.time_out.strftime("%H:%M") if record.time_out else None,
            "break_in": record.break_in.strftime("%H:%M") if record.break_in else None,
            "break_out": record.break_out.strftime("%H:%M") if record.break_out else None,
            "total_hours": record.total_hours,
            "overtime_hours": record.overtime_hours,
            "status": record.status,
            "remarks": record.remarks,
            "is_manual_entry": record.is_manual_entry
        })

    return {
        "records": formatted_records,
        "total": total,
        "page": filters.page,
        "limit": filters.limit,
        "pages": (total + filters.limit - 1) // filters.limit
    }


def get_dtr_by_id(db: Session, dtr_id: int) -> Optional[DailyTimeRecord]:
    """Get single DTR record by ID"""
    return db.query(DailyTimeRecord).filter(DailyTimeRecord.id == dtr_id).first()


def create_dtr_record(db: Session, dtr_data: DTRCreate) -> DailyTimeRecord:
    """Create a new DTR record"""
    dtr = DailyTimeRecord(
        user_id=dtr_data.user_id,
        date=dtr_data.date,
        scheduled_shift=dtr_data.scheduled_shift,
        time_in=dtr_data.time_in,
        time_out=dtr_data.time_out,
        break_in=dtr_data.break_in,
        break_out=dtr_data.break_out,
        total_hours=dtr_data.total_hours,
        overtime_hours=dtr_data.overtime_hours,
        status=dtr_data.status,
        remarks=dtr_data.remarks,
        is_manual_entry=dtr_data.is_manual_entry
    )
    db.add(dtr)
    db.commit()
    db.refresh(dtr)
    return dtr


def update_dtr_record(db: Session, dtr_id: int, dtr_data: DTRUpdate) -> Optional[DailyTimeRecord]:
    """Update an existing DTR record"""
    dtr = get_dtr_by_id(db, dtr_id)
    if not dtr:
        return None

    update_data = dtr_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dtr, field, value)

    db.commit()
    db.refresh(dtr)
    return dtr


def delete_dtr_record(db: Session, dtr_id: int) -> bool:
    """Delete a DTR record"""
    dtr = get_dtr_by_id(db, dtr_id)
    if not dtr:
        return False

    db.delete(dtr)
    db.commit()
    return True


def get_dtr_statistics(db: Session, date_from: Optional[date] = None, date_to: Optional[date] = None) -> Dict[str, Any]:
    """Get DTR statistics"""
    query = db.query(DailyTimeRecord)

    if date_from:
        query = query.filter(DailyTimeRecord.date >= date_from)
    if date_to:
        query = query.filter(DailyTimeRecord.date <= date_to)

    records = query.all()
    total = len(records)

    present_count = sum(1 for r in records if r.status == "Present")
    late_count = sum(1 for r in records if r.status == "Late")
    absent_count = sum(1 for r in records if r.status == "Absent")
    incomplete_count = sum(1 for r in records if r.status == "Incomplete")
    on_leave_count = sum(1 for r in records if r.status == "On Leave")

    # Calculate total overtime
    total_overtime = 0.0
    total_hours_sum = 0.0
    hours_count = 0

    for r in records:
        if r.overtime_hours:
            try:
                total_overtime += float(r.overtime_hours)
            except ValueError:
                pass
        if r.total_hours:
            try:
                total_hours_sum += float(r.total_hours)
                hours_count += 1
            except ValueError:
                pass

    avg_hours = total_hours_sum / hours_count if hours_count > 0 else 0.0

    return {
        "total_records": total,
        "present_count": present_count,
        "late_count": late_count,
        "absent_count": absent_count,
        "incomplete_count": incomplete_count,
        "on_leave_count": on_leave_count,
        "total_overtime_hours": round(total_overtime, 2),
        "average_hours_per_day": round(avg_hours, 2)
    }


def get_filter_options(db: Session) -> Dict[str, List[str]]:
    """Get unique values for filter dropdowns"""
    # Get unique campaigns from users with DTR records
    campaigns = db.query(User.campaign).join(DailyTimeRecord).filter(User.campaign.isnot(None)).distinct().all()

    # Get unique shifts
    shifts = db.query(DailyTimeRecord.scheduled_shift).filter(DailyTimeRecord.scheduled_shift.isnot(None)).distinct().all()

    # Get unique statuses
    statuses = db.query(DailyTimeRecord.status).distinct().all()

    return {
        "campaigns": sorted([c[0] for c in campaigns if c[0]]),
        "shifts": sorted([s[0] for s in shifts if s[0]]),
        "statuses": sorted([s[0] for s in statuses if s[0]])
    }


def bulk_create_dtr_records(db: Session, records: List[DTRCreate]) -> int:
    """Bulk create DTR records"""
    created_count = 0
    for record_data in records:
        dtr = DailyTimeRecord(
            user_id=record_data.user_id,
            date=record_data.date,
            scheduled_shift=record_data.scheduled_shift,
            time_in=record_data.time_in,
            time_out=record_data.time_out,
            break_in=record_data.break_in,
            break_out=record_data.break_out,
            total_hours=record_data.total_hours,
            overtime_hours=record_data.overtime_hours,
            status=record_data.status,
            remarks=record_data.remarks,
            is_manual_entry=record_data.is_manual_entry
        )
        db.add(dtr)
        created_count += 1

    db.commit()
    return created_count
