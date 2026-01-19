from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import Optional, List, Tuple
from datetime import date, datetime
from app.models.user import User
from app.models.rbac import Role
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeFilter, EmployeeStatus
from app.core.security import get_password_hash
from app.services.rbac_service import get_role_by_name


def calculate_tenure_months(date_of_joining: date) -> int:
    """Calculate tenure in months from date of joining"""
    if not date_of_joining:
        return 0
    
    today = date.today()
    years = today.year - date_of_joining.year
    months = today.month - date_of_joining.month
    
    # Adjust if the day hasn't occurred yet this month
    if today.day < date_of_joining.day:
        months -= 1
    
    return years * 12 + months


def create_employee(db: Session, employee_data: EmployeeCreate) -> User:
    """Create a new employee"""
    # Get role
    role = get_role_by_name(db, employee_data.role_name)
    if not role:
        raise ValueError(f"Role '{employee_data.role_name}' not found")
    
    # Check if employee_no already exists
    existing_emp = db.query(User).filter(User.employee_no == employee_data.employee_no).first()
    if existing_emp:
        raise ValueError("Employee number already exists")
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == employee_data.email).first()
    if existing_email:
        raise ValueError("Email already exists")
    
    # Calculate tenure if date_of_joining is provided
    tenure_months = calculate_tenure_months(employee_data.date_of_joining) if employee_data.date_of_joining else 0
    
    # Create employee
    db_employee = User(
        employee_no=employee_data.employee_no,
        full_name=employee_data.full_name,
        email=employee_data.email,
        hashed_password=get_password_hash(employee_data.password),
        role_id=role.id,
        campaign=employee_data.campaign,
        department=employee_data.department,
        date_of_joining=employee_data.date_of_joining,
        last_working_date=employee_data.last_working_date,
        phone_no=employee_data.phone_no,
        personal_email=employee_data.personal_email,
        client_email=employee_data.client_email,
        tenure_months=tenure_months,
        assessment_due_date=employee_data.assessment_due_date,
        regularization_date=employee_data.regularization_date,
        employee_status=employee_data.employee_status,
        is_active=True
    )
    
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee


def get_employee_by_id(db: Session, employee_id: int) -> Optional[User]:
    """Get employee by ID"""
    return db.query(User).filter(User.id == employee_id).first()


def get_employee_by_employee_no(db: Session, employee_no: str) -> Optional[User]:
    """Get employee by employee number"""
    return db.query(User).filter(User.employee_no == employee_no).first()


def update_employee(db: Session, employee_id: int, employee_data: EmployeeUpdate) -> User:
    """Update employee details"""
    db_employee = get_employee_by_id(db, employee_id)
    if not db_employee:
        raise ValueError("Employee not found")
    
    # Check for unique constraints if being updated
    update_data = employee_data.model_dump(exclude_unset=True)
    
    if "employee_no" in update_data and update_data["employee_no"] != db_employee.employee_no:
        existing = db.query(User).filter(User.employee_no == update_data["employee_no"]).first()
        if existing:
            raise ValueError("Employee number already exists")
    
    if "email" in update_data and update_data["email"] != db_employee.email:
        existing = db.query(User).filter(User.email == update_data["email"]).first()
        if existing:
            raise ValueError("Email already exists")
    
    # Update role if provided
    if "role_name" in update_data:
        role = get_role_by_name(db, update_data["role_name"])
        if not role:
            raise ValueError(f"Role '{update_data['role_name']}' not found")
        db_employee.role_id = role.id
        del update_data["role_name"]
    
    # Update other fields
    for field, value in update_data.items():
        setattr(db_employee, field, value)
    
    # Recalculate tenure if date_of_joining was updated
    if "date_of_joining" in update_data and update_data["date_of_joining"]:
        db_employee.tenure_months = calculate_tenure_months(update_data["date_of_joining"])
    
    db.commit()
    db.refresh(db_employee)
    return db_employee


def delete_employee(db: Session, employee_id: int) -> bool:
    """Delete employee"""
    db_employee = get_employee_by_id(db, employee_id)
    if not db_employee:
        return False
    
    db.delete(db_employee)
    db.commit()
    return True


def get_employees_with_filters(db: Session, filters: EmployeeFilter) -> Tuple[List[User], int]:
    """Get employees with filtering, searching, and pagination - excludes admin users"""
    admin_role = db.query(Role).filter(Role.name == 'admin').first()
    query = db.query(User).join(Role, User.role_id == Role.id, isouter=True)
    
    # Exclude admin users from employee directory
    if admin_role:
        query = query.filter(User.role_id != admin_role.id)
    
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
    
    # Apply specific filters
    if filters.campaign:
        query = query.filter(User.campaign == filters.campaign)
    
    if filters.department:
        query = query.filter(User.department == filters.department)
    
    if filters.employee_status:
        # Handle both enum and string values
        status_value = filters.employee_status.value if hasattr(filters.employee_status, 'value') else str(filters.employee_status)
        query = query.filter(User.employee_status == status_value)
    
    if filters.is_active is not None:
        query = query.filter(User.is_active == filters.is_active)
    
    if filters.role_name:
        query = query.filter(Role.name == filters.role_name)
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply sorting
    sort_column = User.full_name  # Default sort
    if filters.sort_by:
        sort_mapping = {
            'full_name': User.full_name,
            'campaign': User.campaign,
            'date_of_joining': User.date_of_joining,
            'last_working_date': User.last_working_date,
            'employee_status': User.employee_status,
            'phone_no': User.phone_no
        }
        sort_column = sort_mapping.get(filters.sort_by, User.full_name)
    
    if filters.sort_order and filters.sort_order.lower() == 'desc':
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()
    
    # Apply pagination
    offset = (filters.page - 1) * filters.limit
    employees = query.order_by(sort_column).offset(offset).limit(filters.limit).all()
    
    return employees, total_count


def get_employee_statistics(db: Session) -> dict:
    """Get employee statistics for dashboard - excludes admin users"""
    admin_role = db.query(Role).filter(Role.name == 'admin').first()
    
    # Base query excluding admin
    base_query = db.query(User)
    if admin_role:
        base_query = base_query.filter(User.role_id != admin_role.id)
    
    total_employees = base_query.count()
    active_employees = base_query.filter(User.is_active == True).count()
    inactive_employees = total_employees - active_employees
    
    # Status breakdown
    status_counts = base_query.with_entities(
        User.employee_status, 
        func.count(User.id)
    ).group_by(User.employee_status).all()
    
    # Department breakdown
    dept_counts = base_query.filter(User.department.isnot(None)).with_entities(
        User.department, 
        func.count(User.id)
    ).group_by(User.department).all()
    
    # Campaign breakdown
    campaign_counts = base_query.filter(User.campaign.isnot(None)).with_entities(
        User.campaign, 
        func.count(User.id)
    ).group_by(User.campaign).all()
    
    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "inactive_employees": inactive_employees,
        "status_breakdown": dict(status_counts),
        "department_breakdown": dict(dept_counts),
        "campaign_breakdown": dict(campaign_counts)
    }


def get_unique_values(db: Session) -> dict:
    """Get unique values for filter dropdowns"""
    result = {
        "campaigns": [],
        "departments": [],
        "roles": [],
        "statuses": ["Active", "Inactive", "On Leave", "Probation", "Terminated", "Resignation Pending", "New Hire"]
    }

    try:
        # Get unique campaigns
        campaigns_result = db.query(User.campaign).filter(User.campaign.isnot(None)).distinct().all()
        result["campaigns"] = sorted(list(set([c[0] for c in campaigns_result if c[0]])))
    except Exception:
        pass

    try:
        # Get unique departments
        departments_result = db.query(User.department).filter(User.department.isnot(None)).distinct().all()
        result["departments"] = sorted(list(set([d[0] for d in departments_result if d[0]])))
    except Exception:
        pass

    try:
        # Get statuses from actual data
        statuses_result = db.query(User.employee_status).filter(User.employee_status.isnot(None)).distinct().all()
        statuses_set = set([str(s[0]) for s in statuses_result if s[0]])
        if statuses_set:
            result["statuses"] = sorted(list(statuses_set))
    except Exception:
        pass

    try:
        # Get all roles
        roles_result = db.query(Role).filter(Role.name != 'admin').all()
        result["roles"] = [{"name": r.name, "display_name": r.display_name} for r in roles_result]
    except Exception:
        pass

    return result


def bulk_update_employee_status(db: Session, employee_ids: List[int], status: EmployeeStatus) -> int:
    """Bulk update employee status"""
    updated = db.query(User).filter(User.id.in_(employee_ids)).update(
        {User.employee_status: status.value}, 
        synchronize_session=False
    )
    db.commit()
    return updated


def get_employees_for_assessment(db: Session, days_ahead: int = 30) -> List[User]:
    """Get employees with assessments due within specified days"""
    target_date = date.today().replace(day=1)  # Start of current month
    from datetime import timedelta
    end_date = target_date + timedelta(days=days_ahead)
    
    return db.query(User).filter(
        and_(
            User.assessment_due_date.isnot(None),
            User.assessment_due_date >= target_date,
            User.assessment_due_date <= end_date,
            User.is_active == True
        )
    ).order_by(User.assessment_due_date).all()