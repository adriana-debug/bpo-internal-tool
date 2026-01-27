from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import engine, get_db, Base
from app.core.config import settings
from app.core.security import create_access_token, decode_token
from app.models.user import User, ShiftSchedule, DailyTimeRecord
from app.models.rbac import Role, Module, RoleModulePermission, UserModulePermission
from app.models.pay_dispute import PayDispute, PayDisputeComment
from app.models.ir_nte_log import IRNTELog
from app.services.auth_service import authenticate_user, create_user, get_user_by_email
from app.services.rbac_service import (
    seed_roles_and_modules,
    get_accessible_modules,
    check_permission,
    get_role_by_name,
    get_all_roles,
    grant_custom_permission,
    revoke_custom_permission
)
from app.services.employee_service import (
    create_employee,
    get_employee_by_id,
    update_employee,
    delete_employee,
    get_employees_with_filters,
    get_employee_statistics,
    get_unique_values,
    bulk_update_employee_status,
    get_employees_for_assessment
)
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeFilter, EmployeeResponse, EmployeeListResponse
from app.schemas.dtr import DTRCreate, DTRUpdate, DTRFilter
from app.services.dtr_service import (
    get_dtr_records,
    get_dtr_by_id,
    create_dtr_record,
    update_dtr_record,
    delete_dtr_record,
    get_dtr_statistics,
    get_filter_options as get_dtr_filter_options,
    bulk_create_dtr_records
)
from app.schemas.pay_dispute import PayDisputeCreate, PayDisputeUpdate, PayDisputeFilter, PayDisputeCommentCreate
from app.services.pay_dispute_service import (
    get_pay_disputes,
    get_pay_dispute_by_id,
    create_pay_dispute,
    update_pay_dispute,
    delete_pay_dispute,
    get_pay_dispute_statistics,
    get_filter_options as get_pay_dispute_filter_options,
    add_comment as add_pay_dispute_comment,
    get_comments as get_pay_dispute_comments
)
from app.schemas.ir_nte_log import IRNTELogCreate, IRNTELogUpdate, IRNTELogFilter
from app.services.shift_schedule_service import ShiftScheduleService
from app.services.ir_nte_service import (
    get_ir_nte_logs,
    get_ir_nte_by_id,
    create_ir_nte_log,
    update_ir_nte_log,
    delete_ir_nte_log,
    get_ir_nte_statistics,
    get_filter_options as get_ir_nte_filter_options
)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BPO Internal Platform")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    print("DEBUG: get_current_user called")
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    email = payload.get("sub")
    if not email:
        return None
    return get_user_by_email(db, email)


def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_permission(module: str, action: str = "view"):
    """Dependency factory for checking permissions"""
    print(f"DEBUG: require_permission factory called for {module}:{action}")
    def check(request: Request, db: Session = Depends(get_db)):
        print(f"DEBUG: require_permission check called for {module}:{action}")
        user = get_current_user(request, db)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        if not check_permission(db, user, module, action):
            raise HTTPException(status_code=403, detail="Permission denied")
        return user
    return check


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password"}
        )

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    modules = get_accessible_modules(db, user)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "modules": modules,
        "current_route": "/dashboard"
    })


# ============== Admin Routes ==============

@app.get("/admin/users", response_class=HTMLResponse)
async def user_management(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("user_management", "view"))
):
    modules = get_accessible_modules(db, user)
    users = db.query(User).all()
    roles = get_all_roles(db)
    
    # Calculate user statistics
    active_users = sum(1 for u in users if u.is_active)
    inactive_users = len(users) - active_users
    
    # Convert roles to JSON-serializable format for the template
    roles_json = [{"id": role.id, "name": role.name} for role in roles]
    
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "user": user,
        "modules": modules,
        "users": users,
        "roles": roles,
        "roles_json": roles_json,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "current_route": "/admin/users"
    })


@app.get("/admin/roles", response_class=HTMLResponse)
async def role_management(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("role_management", "view"))
):
    modules = get_accessible_modules(db, user)
    roles = get_all_roles(db)
    all_modules = db.query(Module).filter(Module.is_active == True).order_by(Module.sort_order).all()
    return templates.TemplateResponse("admin/roles.html", {
        "request": request,
        "user": user,
        "modules": modules,
        "roles": roles,
        "all_modules": all_modules,
        "current_route": "/admin/roles"
    })


# ============== Operations Routes ==============
from app.models.requests import Request as RequestModel
from app.schemas.requests import RequestCreate, RequestOut
from app.services.requests_service import (
    get_requests,
    get_request,
    create_request,
    update_request,
    delete_request
)

@app.get("/operations/requests", response_class=HTMLResponse)
async def requests_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("requests", "view"))
):
    modules = get_accessible_modules(db, user)
    requests_list = get_requests(db)
    return templates.TemplateResponse("operations/requests.html", {
        "request": request,
        "user": user,
        "modules": modules,
        "requests": requests_list,
        "current_route": "/operations/requests"
    })

@app.get("/operations/employee-directory", response_class=HTMLResponse)
async def employee_directory(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("employee_directory", "view"))
):
    modules = get_accessible_modules(db, user)
    return templates.TemplateResponse("operations/employee-directory.html", {
        "request": request,
        "user": user,
        "modules": modules,
        "current_route": "/operations/employee-directory"
    })


@app.get("/operations/schedule", response_class=HTMLResponse)
async def schedule(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("schedule", "view"))
):
    modules = get_accessible_modules(db, user)
    return templates.TemplateResponse("operations/schedule.html", {
        "request": request,
        "user": user,
        "modules": modules,
        "current_route": "/operations/schedule"
    })


@app.get("/operations/dtr", response_class=HTMLResponse)
async def daily_time_record(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("dtr", "view"))
):
    modules = get_accessible_modules(db, user)
    return templates.TemplateResponse("operations/dtr.html", {
        "request": request,
        "user": user,
        "modules": modules,
        "current_route": "/operations/dtr"
    })


@app.get("/operations/pay-disputes", response_class=HTMLResponse)
async def pay_disputes_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pay_disputes", "view"))
):
    modules = get_accessible_modules(db, user)
    return templates.TemplateResponse("operations/pay-disputes.html", {
        "request": request,
        "user": user,
        "modules": modules,
        "current_route": "/operations/pay-disputes"
    })


@app.get("/operations/ir-nte-logs", response_class=HTMLResponse)
async def ir_nte_logs_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("ir_nte_logs", "view"))
):
    modules = get_accessible_modules(db, user)
    return templates.TemplateResponse("operations/ir-nte-logs.html", {
        "request": request,
        "user": user,
        "modules": modules,
        "current_route": "/operations/ir-nte-logs"
    })


# ============== API Endpoints ==============

# Requests API
from fastapi import Body

@app.get("/api/requests", response_model=list[RequestOut])
async def api_get_requests(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("requests", "view"))
):
    return get_requests(db)

@app.post("/api/requests", response_model=RequestOut)
async def api_create_request(
    request_in: RequestCreate = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("requests", "create"))
):
    return create_request(db, user.id, request_in)

@app.get("/api/requests/{request_id}", response_model=RequestOut)
async def api_get_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("requests", "view"))
):
    req = get_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req

@app.put("/api/requests/{request_id}", response_model=RequestOut)
async def api_update_request(
    request_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("requests", "edit"))
):
    req = update_request(db, request_id, data)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req

@app.delete("/api/requests/{request_id}")
async def api_delete_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("requests", "delete"))
):
    ok = delete_request(db, request_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"status": "success"}

@app.get("/api/users/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user_management", "view"))
):
    """Get a single user by ID"""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": target_user.id,
        "email": target_user.email,
        "full_name": target_user.full_name,
        "employee_no": target_user.employee_no,
        "role_id": target_user.role_id,
        "role_name": target_user.role.name if target_user.role else None,
        "department": target_user.department,
        "campaign": target_user.campaign,
        "is_active": target_user.is_active
    }


@app.post("/api/users")
async def create_new_user(
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    employee_no: str = Form(...),
    role_name: str = Form(...),
    department: str = Form(None),
    campaign: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user_management", "create"))
):
    """Create a new user"""
    # Check if email already exists
    existing = get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if employee_no already exists
    existing_emp = db.query(User).filter(User.employee_no == employee_no).first()
    if existing_emp:
        raise HTTPException(status_code=400, detail="Employee number already exists")

    # Get role
    role = get_role_by_name(db, role_name)
    if not role:
        raise HTTPException(status_code=400, detail="Invalid role")

    new_user = create_user(
        db=db,
        email=email,
        password=password,
        full_name=full_name,
        employee_no=employee_no,
        role_id=role.id,
        department=department if department else None,
        campaign=campaign if campaign else None
    )

    return {
        "status": "success",
        "message": f"User {full_name} created successfully",
        "user_id": new_user.id
    }


@app.put("/api/users/{user_id}")
async def update_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user_management", "edit"))
):
    """Update user details"""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    data = await request.json()

    # Update email if provided and different
    if data.get("email") and data["email"] != target_user.email:
        existing = get_user_by_email(db, data["email"])
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        target_user.email = data["email"]

    # Update employee_no if provided and different
    if data.get("employee_no") and data["employee_no"] != target_user.employee_no:
        existing = db.query(User).filter(User.employee_no == data["employee_no"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="Employee number already in use")
        target_user.employee_no = data["employee_no"]

    # Update other fields
    if data.get("full_name"):
        target_user.full_name = data["full_name"]
    if data.get("department") is not None:
        target_user.department = data["department"] if data["department"] else None
    if data.get("campaign") is not None:
        target_user.campaign = data["campaign"] if data["campaign"] else None
    if data.get("is_active") is not None:
        target_user.is_active = data["is_active"]

    # Update role if provided
    if data.get("role_name"):
        role = get_role_by_name(db, data["role_name"])
        if role:
            target_user.role_id = role.id

    # Update password if provided
    if data.get("password"):
        from app.core.security import get_password_hash
        target_user.hashed_password = get_password_hash(data["password"])

    db.commit()
    return {"status": "success", "message": "User updated successfully"}


@app.delete("/api/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user_management", "delete"))
):
    """Delete a user"""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-deletion
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    # Delete user's custom permissions first
    db.query(UserModulePermission).filter(UserModulePermission.user_id == user_id).delete()

    # Delete the user
    db.delete(target_user)
    db.commit()

    return {"status": "success", "message": "User deleted successfully"}


@app.patch("/api/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user_management", "edit"))
):
    """Toggle user active status"""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-deactivation
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    target_user.is_active = not target_user.is_active
    db.commit()

    status = "activated" if target_user.is_active else "deactivated"
    return {"status": "success", "message": f"User {status} successfully", "is_active": target_user.is_active}


@app.post("/api/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user_management", "edit"))
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    role = get_role_by_name(db, role_name)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    target_user.role_id = role.id
    db.commit()
    return {"status": "success", "message": f"Role updated to {role.display_name}"}


@app.post("/api/users/{user_id}/permissions")
async def update_user_permissions(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user_management", "edit"))
):
    data = await request.json()
    module_name = data.get("module")
    permissions = data.get("permissions", {})

    if not module_name:
        raise HTTPException(status_code=400, detail="Module name required")

    try:
        grant_custom_permission(
            db=db,
            user_id=user_id,
            module_name=module_name,
            can_view=permissions.get("view", False),
            can_create=permissions.get("create", False),
            can_edit=permissions.get("edit", False),
            can_delete=permissions.get("delete", False),
            granted_by=current_user.id
        )
        return {"status": "success", "message": "Custom permissions updated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/users/{user_id}/permissions/{module_name}")
async def remove_user_permissions(
    user_id: int,
    module_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user_management", "edit"))
):
    revoke_custom_permission(db, user_id, module_name)
    return {"status": "success", "message": "Custom permissions revoked"}


# ============== Employee Directory API Endpoints ==============

@app.get("/api/employees/statistics")
async def get_employee_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("employee_directory", "view"))
):
    """Get employee statistics"""
    return get_employee_statistics(db)


@app.get("/api/employees/filter-options")
async def get_filter_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("employee_directory", "view"))
):
    """Get unique values for filter dropdowns"""
    return get_unique_values(db)


@app.get("/api/employees/assessments-due")
async def get_assessments_due(
    days_ahead: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("employee_directory", "view"))
):
    """Get employees with assessments due within specified days"""
    employees = get_employees_for_assessment(db, days_ahead)
    
    result = []
    for emp in employees:
        result.append({
            "id": emp.id,
            "employee_no": emp.employee_no,
            "full_name": emp.full_name,
            "department": emp.department,
            "campaign": emp.campaign,
            "assessment_due_date": emp.assessment_due_date.isoformat() if emp.assessment_due_date else None,
            "tenure_months": emp.tenure_months
        })
    
    return {"employees": result, "count": len(result)}


@app.get("/api/employees", response_model=EmployeeListResponse)
async def get_employees(
    search: str = None,
    campaign: str = None,
    department: str = None,
    employee_status: str = None,
    is_active: bool = None,
    role_name: str = None,
    page: int = 1,
    limit: int = 50,
    sort_by: str = None,
    sort_order: str = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("employee_directory", "view"))
):
    """Get employees with filtering, pagination, and sorting"""
    filters = EmployeeFilter(
        search=search,
        campaign=campaign,
        department=department,
        employee_status=employee_status,
        is_active=is_active,
        role_name=role_name,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    employees, total_count = get_employees_with_filters(db, filters)
    total_pages = (total_count + filters.limit - 1) // filters.limit
    
    employee_responses = []
    for emp in employees:
        employee_responses.append(EmployeeResponse(
            id=emp.id,
            employee_no=emp.employee_no,
            full_name=emp.full_name,
            email=emp.email,
            campaign=emp.campaign,
            department=emp.department,
            date_of_joining=emp.date_of_joining,
            last_working_date=emp.last_working_date,
            phone_no=emp.phone_no,
            personal_email=emp.personal_email,
            client_email=emp.client_email,
            tenure_months=emp.tenure_months,
            assessment_due_date=emp.assessment_due_date,
            regularization_date=emp.regularization_date,
            employee_status=emp.employee_status,
            role_name=emp.role.display_name if emp.role else None,
            is_active=emp.is_active,
            created_at=emp.created_at.isoformat() if emp.created_at else None,
            updated_at=emp.updated_at.isoformat() if emp.updated_at else None
        ))
    
    return EmployeeListResponse(
        employees=employee_responses,
        total_count=total_count,
        page=filters.page,
        limit=filters.limit,
        total_pages=total_pages
    )


@app.get("/api/employees/{employee_id}")
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("employee_directory", "view"))
):
    """Get a single employee by ID"""
    employee = get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {
        "id": employee.id,
        "employee_no": employee.employee_no,
        "full_name": employee.full_name,
        "email": employee.email,
        "campaign": employee.campaign,
        "department": employee.department,
        "date_of_joining": employee.date_of_joining.isoformat() if employee.date_of_joining else None,
        "last_working_date": employee.last_working_date.isoformat() if employee.last_working_date else None,
        "phone_no": employee.phone_no,
        "personal_email": employee.personal_email,
        "client_email": employee.client_email,
        "tenure_months": employee.tenure_months,
        "assessment_due_date": employee.assessment_due_date.isoformat() if employee.assessment_due_date else None,
        "regularization_date": employee.regularization_date.isoformat() if employee.regularization_date else None,
        "employee_status": employee.employee_status,
        "role_name": employee.role.display_name if employee.role else None,
        "role_id": employee.role_id,
        "is_active": employee.is_active,
        "created_at": employee.created_at.isoformat() if employee.created_at else None,
        "updated_at": employee.updated_at.isoformat() if employee.updated_at else None
    }


@app.post("/api/employees")
async def create_new_employee(
    employee_no: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role_name: str = Form(...),
    campaign: str = Form(None),
    department: str = Form(None),
    date_of_joining: str = Form(None),
    last_working_date: str = Form(None),
    phone_no: str = Form(None),
    personal_email: str = Form(None),
    client_email: str = Form(None),
    assessment_due_date: str = Form(None),
    regularization_date: str = Form(None),
    employee_status: str = Form("Active"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("employee_directory", "create"))
):
    """Create a new employee"""
    from datetime import datetime
    
    try:
        # Parse date fields
        date_of_joining_parsed = datetime.strptime(date_of_joining, "%Y-%m-%d").date() if date_of_joining else None
        last_working_date_parsed = datetime.strptime(last_working_date, "%Y-%m-%d").date() if last_working_date else None
        assessment_due_date_parsed = datetime.strptime(assessment_due_date, "%Y-%m-%d").date() if assessment_due_date else None
        regularization_date_parsed = datetime.strptime(regularization_date, "%Y-%m-%d").date() if regularization_date else None
        
        employee_data = EmployeeCreate(
            employee_no=employee_no,
            full_name=full_name,
            email=email,
            password=password,
            role_name=role_name,
            campaign=campaign if campaign else None,
            department=department if department else None,
            date_of_joining=date_of_joining_parsed,
            last_working_date=last_working_date_parsed,
            phone_no=phone_no if phone_no else None,
            personal_email=personal_email if personal_email else None,
            client_email=client_email if client_email else None,
            assessment_due_date=assessment_due_date_parsed,
            regularization_date=regularization_date_parsed,
            employee_status=employee_status
        )
        
        new_employee = create_employee(db, employee_data)
        return {
            "status": "success",
            "message": f"Employee {full_name} created successfully",
            "employee_id": new_employee.id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error creating employee")


@app.put("/api/employees/{employee_id}")
async def update_employee_details(
    employee_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("employee_directory", "edit"))
):
    """Update employee details"""
    try:
        data = await request.json()
        
        # Parse date fields if they exist
        if data.get("date_of_joining"):
            data["date_of_joining"] = datetime.strptime(data["date_of_joining"], "%Y-%m-%d").date()
        if data.get("last_working_date"):
            data["last_working_date"] = datetime.strptime(data["last_working_date"], "%Y-%m-%d").date()
        if data.get("assessment_due_date"):
            data["assessment_due_date"] = datetime.strptime(data["assessment_due_date"], "%Y-%m-%d").date()
        if data.get("regularization_date"):
            data["regularization_date"] = datetime.strptime(data["regularization_date"], "%Y-%m-%d").date()
        
        employee_update = EmployeeUpdate(**data)
        updated_employee = update_employee(db, employee_id, employee_update)
        
        return {"status": "success", "message": "Employee updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error updating employee")


@app.delete("/api/employees/{employee_id}")
async def delete_employee_record(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("employee_directory", "delete"))
):
    """Delete an employee"""
    # Prevent self-deletion
    if employee_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own record")
    
    success = delete_employee(db, employee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {"status": "success", "message": "Employee deleted successfully"}


@app.post("/api/employees/bulk-status-update")
async def bulk_update_status(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("employee_directory", "edit"))
):
    """Bulk update employee status"""
    data = await request.json()
    employee_ids = data.get("employee_ids", [])
    status = data.get("status")
    
    if not employee_ids or not status:
        raise HTTPException(status_code=400, detail="Employee IDs and status are required")
    
    try:
        updated_count = bulk_update_employee_status(db, employee_ids, status)
        return {
            "status": "success", 
            "message": f"Updated {updated_count} employees to {status}",
            "updated_count": updated_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error updating employee status")


# ============== Shift Schedule API ==============

@app.get("/api/shift-schedule")
async def get_shift_schedule(
    week: str = None,
    search: str = None,
    campaign: str = None,
    shift: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("schedule", "view"))
):
    """Get weekly shift schedule with filters"""
    try:
        # Parse week date (should be Monday of the week)
        if week:
            week_start = datetime.fromisoformat(week)
        else:
            # Default to current week's Monday
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())

        # Get schedules
        schedules = ShiftScheduleService.get_weekly_schedule(
            db=db,
            week_start_date=week_start,
            search=search,
            campaign=campaign,
            shift=shift
        )

        return {
            "status": "success",
            "week_start": week_start.date(),
            "schedules": schedules
        }
    except Exception as e:
        import traceback
        import os
        error_msg = f"Error loading schedule: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        # Log to a file we can definitely read
        with open("app_error.log", "a") as f:
            f.write(f"\n--- API Error at {datetime.now()} ---\n")
            f.write(error_msg)
        raise HTTPException(status_code=500, detail=f"Error loading schedule: {str(e)}")


@app.get("/api/shift-schedule/statistics")
async def get_shift_schedule_statistics(
    week: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("schedule", "view"))
):
    """Get shift schedule statistics"""
    try:
        if week:
            week_start = datetime.fromisoformat(week)
        else:
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())

        return ShiftScheduleService.get_schedule_statistics(db, week_start)
    except Exception as e:
        print(f"Error loading statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading statistics: {str(e)}")


@app.get("/api/shift-schedule/filter-options")
async def get_shift_schedule_filter_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("schedule", "view"))
):
    """Get filter options for shift schedule"""
    from app.services.shift_schedule_service import ShiftScheduleService

    return ShiftScheduleService.get_filter_options(db)


@app.get("/api/shift-schedule/export")
async def export_shift_schedule_csv(
    week: str = None,
    search: str = None,
    campaign: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("schedule", "view"))
):
    """Export shift schedules to CSV"""
    from app.services.shift_schedule_service import ShiftScheduleService
    from datetime import datetime, timedelta
    import csv
    import io

    try:
        if week:
            week_start = datetime.fromisoformat(week)
        else:
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())

        schedules = ShiftScheduleService.get_schedules_for_export(
            db=db,
            week_start_date=week_start,
            search=search,
            campaign=campaign
        )

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Employee No",
            "Employee Name",
            "Campaign",
            "Date",
            "Day of Week",
            "Shift Time",
            "Published",
            "Notes"
        ])

        # Write data
        for schedule in schedules:
            writer.writerow([
                schedule["employee_no"],
                schedule["employee_name"],
                schedule["campaign"],
                schedule["date"],
                schedule["day_of_week"],
                schedule["shift_time"],
                schedule["is_published"],
                schedule["notes"]
            ])

        output.seek(0)
        week_str = week_start.strftime('%Y-%m-%d')
        filename = f"shift_schedule_{week_str}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        print(f"Error exporting schedule: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting schedule: {str(e)}")


@app.get("/api/shift-schedule/{schedule_id}")
async def get_single_shift_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("schedule", "view"))
):
    """Get a single shift schedule by ID"""
    from app.services.shift_schedule_service import ShiftScheduleService

    schedule = ShiftScheduleService.get_schedule_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return {
        "id": schedule.id,
        "user_id": schedule.user_id,
        "employee_name": schedule.user.full_name if schedule.user else None,
        "employee_no": schedule.user.employee_no if schedule.user else None,
        "campaign": schedule.campaign or (schedule.user.campaign if schedule.user else None),
        "schedule_date": schedule.schedule_date.isoformat() if schedule.schedule_date else None,
        "day_of_week": schedule.day_of_week,
        "shift_time": schedule.shift_time,
        "is_published": schedule.is_published,
        "notes": schedule.notes
    }


@app.delete("/api/shift-schedule/{schedule_id}")
async def delete_shift_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("schedule", "delete"))
):
    """Delete a shift schedule"""
    from app.services.shift_schedule_service import ShiftScheduleService

    if not ShiftScheduleService.delete_schedule(db, schedule_id):
        raise HTTPException(status_code=404, detail="Schedule not found")

    return {"status": "success", "message": "Schedule deleted successfully"}


@app.post("/api/shift-schedule/save")
async def save_shift_schedule(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("schedule", "edit"))
):
    """Save a shift schedule"""
    from app.services.shift_schedule_service import ShiftScheduleService
    from datetime import datetime
    
    data = await request.json()
    
    try:
        schedule = ShiftScheduleService.save_shift(
            db=db,
            user_id=data['user_id'],
            schedule_date=datetime.fromisoformat(data['schedule_date']),
            shift_time=data['shift_time'],
            campaign=data['campaign'],
            notes=data.get('notes')
        )
        
        return {
            "status": "success",
            "message": "Schedule saved successfully",
            "schedule": {
                "id": schedule.id,
                "user_id": schedule.user_id,
                "schedule_date": schedule.schedule_date.isoformat(),
                "shift_time": schedule.shift_time,
                "campaign": schedule.campaign
            }
        }
    except Exception as e:
        print(f"Error saving schedule: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving schedule: {str(e)}")


@app.post("/api/shift-schedule/publish")
async def publish_shift_schedule(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("schedule", "edit"))
):
    """Publish all schedules for a week"""
    from app.services.shift_schedule_service import ShiftScheduleService
    from datetime import datetime, timedelta
    
    data = await request.json()
    
    try:
        if 'week' not in data:
            raise HTTPException(status_code=400, detail="Week date is required")
        
        week_start = datetime.fromisoformat(data['week'])
        updated_count = ShiftScheduleService.publish_schedules(db, week_start)
        
        return {
            "status": "success",
            "message": f"Published {updated_count} schedules",
            "updated_count": updated_count
        }
    except Exception as e:
        print(f"Error publishing schedule: {e}")
        raise HTTPException(status_code=500, detail=f"Error publishing schedule: {str(e)}")


@app.post("/api/shift-schedule/upload")
async def upload_shift_schedule(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("schedule", "edit"))
):
    """Bulk upload shift schedules from file"""
    from app.services.shift_schedule_service import ShiftScheduleService
    
    data = await request.json()
    schedules_data = data.get('schedules', [])
    
    try:
        count = ShiftScheduleService.bulk_upload_schedules(db, schedules_data)
        
        return {
            "status": "success",
            "message": f"Uploaded {count} schedules",
            "count": count
        }
    except Exception as e:
        print(f"Error uploading schedule: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading schedule: {str(e)}")


# ============== DTR API Endpoints ==============

@app.get("/api/dtr")
async def get_dtr_list(
    request: Request,
    search: str = None,
    campaign: str = None,
    date_from: str = None,
    date_to: str = None,
    shift: str = None,
    status: str = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("dtr", "view"))
):
    """Get DTR records with filtering and pagination"""
    from datetime import datetime

    filters = DTRFilter(
        search=search,
        campaign=campaign,
        date_from=datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None,
        date_to=datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None,
        shift=shift,
        status=status,
        page=page,
        limit=limit
    )

    return get_dtr_records(db, filters)


@app.get("/api/dtr/statistics")
async def get_dtr_stats(
    date_from: str = None,
    date_to: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("dtr", "view"))
):
    """Get DTR statistics"""
    from datetime import datetime

    df = datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None
    dt = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None

    return get_dtr_statistics(db, df, dt)


@app.get("/api/dtr/filter-options")
async def get_dtr_filters(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("dtr", "view"))
):
    """Get unique values for DTR filters"""
    return get_dtr_filter_options(db)


@app.get("/api/dtr/export")
async def export_dtr_csv(
    request: Request,
    search: str = None,
    campaign: str = None,
    date_from: str = None,
    date_to: str = None,
    shift: str = None,
    status: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("dtr", "view"))
):
    """Export DTR records to CSV"""
    from datetime import datetime
    import csv
    import io

    # Build filters (no pagination for export)
    filters = DTRFilter(
        search=search,
        campaign=campaign,
        date_from=datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None,
        date_to=datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None,
        shift=shift,
        status=status,
        page=1,
        limit=100000  # Get all records
    )

    result = get_dtr_records(db, filters)
    records = result["records"]

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "Employee No",
        "Employee Name",
        "Campaign",
        "Date",
        "Scheduled Shift",
        "Time In",
        "Time Out",
        "Break In",
        "Break Out",
        "Total Hours",
        "Overtime Hours",
        "Status",
        "Remarks"
    ])

    # Write data rows
    for record in records:
        writer.writerow([
            record["employee_no"],
            record["employee_name"],
            record["campaign"],
            record["date"],
            record["scheduled_shift"] or "",
            record["time_in"] or "",
            record["time_out"] or "",
            record["break_in"] or "",
            record["break_out"] or "",
            record["total_hours"] or "",
            record["overtime_hours"] or "",
            record["status"],
            record["remarks"] or ""
        ])

    output.seek(0)

    # Generate filename with date range or current date
    if date_from and date_to:
        filename = f"dtr_export_{date_from}_to_{date_to}.csv"
    else:
        filename = f"dtr_export_{datetime.now().strftime('%Y-%m-%d')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/api/dtr/{dtr_id}")
async def get_single_dtr(
    dtr_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("dtr", "view"))
):
    """Get single DTR record"""
    dtr = get_dtr_by_id(db, dtr_id)
    if not dtr:
        raise HTTPException(status_code=404, detail="DTR record not found")

    return {
        "id": dtr.id,
        "user_id": dtr.user_id,
        "employee_name": dtr.user.full_name if dtr.user else None,
        "employee_no": dtr.user.employee_no if dtr.user else None,
        "campaign": dtr.user.campaign if dtr.user else None,
        "date": dtr.date.isoformat() if dtr.date else None,
        "scheduled_shift": dtr.scheduled_shift,
        "time_in": dtr.time_in.strftime("%H:%M") if dtr.time_in else None,
        "time_out": dtr.time_out.strftime("%H:%M") if dtr.time_out else None,
        "break_in": dtr.break_in.strftime("%H:%M") if dtr.break_in else None,
        "break_out": dtr.break_out.strftime("%H:%M") if dtr.break_out else None,
        "total_hours": dtr.total_hours,
        "overtime_hours": dtr.overtime_hours,
        "status": dtr.status,
        "remarks": dtr.remarks,
        "is_manual_entry": dtr.is_manual_entry
    }


@app.post("/api/dtr")
async def create_dtr(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("dtr", "create"))
):
    """Create a new DTR record"""
    from datetime import datetime

    data = await request.json()

    dtr_data = DTRCreate(
        user_id=data["user_id"],
        date=datetime.strptime(data["date"], "%Y-%m-%d").date(),
        scheduled_shift=data.get("scheduled_shift"),
        time_in=datetime.strptime(data["time_in"], "%H:%M").time() if data.get("time_in") else None,
        time_out=datetime.strptime(data["time_out"], "%H:%M").time() if data.get("time_out") else None,
        break_in=datetime.strptime(data["break_in"], "%H:%M").time() if data.get("break_in") else None,
        break_out=datetime.strptime(data["break_out"], "%H:%M").time() if data.get("break_out") else None,
        total_hours=data.get("total_hours"),
        overtime_hours=data.get("overtime_hours"),
        status=data.get("status", "Present"),
        remarks=data.get("remarks"),
        is_manual_entry=data.get("is_manual_entry", True)
    )

    dtr = create_dtr_record(db, dtr_data)
    return {"status": "success", "id": dtr.id}


@app.put("/api/dtr/{dtr_id}")
async def update_dtr(
    dtr_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("dtr", "edit"))
):
    """Update a DTR record"""
    from datetime import datetime

    data = await request.json()

    update_data = {}
    if "scheduled_shift" in data:
        update_data["scheduled_shift"] = data["scheduled_shift"]
    if "time_in" in data:
        update_data["time_in"] = datetime.strptime(data["time_in"], "%H:%M").time() if data["time_in"] else None
    if "time_out" in data:
        update_data["time_out"] = datetime.strptime(data["time_out"], "%H:%M").time() if data["time_out"] else None
    if "break_in" in data:
        update_data["break_in"] = datetime.strptime(data["break_in"], "%H:%M").time() if data["break_in"] else None
    if "break_out" in data:
        update_data["break_out"] = datetime.strptime(data["break_out"], "%H:%M").time() if data["break_out"] else None
    if "total_hours" in data:
        update_data["total_hours"] = data["total_hours"]
    if "overtime_hours" in data:
        update_data["overtime_hours"] = data["overtime_hours"]
    if "status" in data:
        update_data["status"] = data["status"]
    if "remarks" in data:
        update_data["remarks"] = data["remarks"]

    dtr_update = DTRUpdate(**update_data)
    dtr = update_dtr_record(db, dtr_id, dtr_update)

    if not dtr:
        raise HTTPException(status_code=404, detail="DTR record not found")

    return {"status": "success"}


@app.delete("/api/dtr/{dtr_id}")
async def delete_dtr(
    dtr_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("dtr", "delete"))
):
    """Delete a DTR record"""
    if not delete_dtr_record(db, dtr_id):
        raise HTTPException(status_code=404, detail="DTR record not found")

    return {"status": "success"}


@app.post("/api/dtr/upload")
async def upload_dtr(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("dtr", "create"))
):
    """Bulk upload DTR records"""
    from datetime import datetime

    data = await request.json()
    records = data.get("records", [])

    dtr_records = []
    for record in records:
        dtr_data = DTRCreate(
            user_id=record["user_id"],
            date=datetime.strptime(record["date"], "%Y-%m-%d").date(),
            scheduled_shift=record.get("scheduled_shift"),
            time_in=datetime.strptime(record["time_in"], "%H:%M").time() if record.get("time_in") else None,
            time_out=datetime.strptime(record["time_out"], "%H:%M").time() if record.get("time_out") else None,
            break_in=datetime.strptime(record["break_in"], "%H:%M").time() if record.get("break_in") else None,
            break_out=datetime.strptime(record["break_out"], "%H:%M").time() if record.get("break_out") else None,
            total_hours=record.get("total_hours"),
            overtime_hours=record.get("overtime_hours"),
            status=record.get("status", "Present"),
            remarks=record.get("remarks"),
            is_manual_entry=record.get("is_manual_entry", False)
        )
        dtr_records.append(dtr_data)

    count = bulk_create_dtr_records(db, dtr_records)
    return {"status": "success", "created": count}


# ============== Pay Dispute API Endpoints ==============

@app.get("/api/pay-disputes")
async def get_pay_disputes_list(
    request: Request,
    search: str = None,
    status: str = None,
    dispute_type: str = None,
    priority: str = None,
    campaign: str = None,
    assigned_to: int = None,
    date_from: str = None,
    date_to: str = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pay_disputes", "view"))
):
    """Get pay disputes with filtering and pagination"""
    from datetime import datetime

    filters = PayDisputeFilter(
        search=search,
        status=status,
        dispute_type=dispute_type,
        priority=priority,
        campaign=campaign,
        assigned_to=assigned_to,
        date_from=datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None,
        date_to=datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None,
        page=page,
        limit=limit
    )

    return get_pay_disputes(db, filters)


@app.get("/api/pay-disputes/statistics")
async def get_pay_disputes_stats(
    date_from: str = None,
    date_to: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pay_disputes", "view"))
):
    """Get pay dispute statistics"""
    from datetime import datetime

    df = datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None
    dt = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None

    return get_pay_dispute_statistics(db, df, dt)


@app.get("/api/pay-disputes/filter-options")
async def get_pay_disputes_filters(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pay_disputes", "view"))
):
    """Get unique values for pay dispute filters"""
    return get_pay_dispute_filter_options(db)


@app.get("/api/pay-disputes/export")
async def export_pay_disputes_csv(
    request: Request,
    search: str = None,
    status: str = None,
    dispute_type: str = None,
    priority: str = None,
    campaign: str = None,
    date_from: str = None,
    date_to: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pay_disputes", "view"))
):
    """Export pay disputes to CSV"""
    from datetime import datetime
    import csv
    import io

    filters = PayDisputeFilter(
        search=search,
        status=status,
        dispute_type=dispute_type,
        priority=priority,
        campaign=campaign,
        date_from=datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None,
        date_to=datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None,
        page=1,
        limit=100000
    )

    result = get_pay_disputes(db, filters)
    disputes = result["disputes"]

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Ticket No", "Employee No", "Employee Name", "Campaign",
        "Dispute Type", "Pay Period", "Disputed Amount", "Subject",
        "Status", "Priority", "Assigned To", "Resolution Amount",
        "Resolved Date", "Created Date"
    ])

    for d in disputes:
        writer.writerow([
            d["ticket_no"],
            d["employee_no"],
            d["employee_name"],
            d["campaign"],
            d["dispute_type"],
            d["pay_period"],
            d["disputed_amount"] or "",
            d["subject"],
            d["status"],
            d["priority"],
            d["assignee_name"] or "",
            d["resolution_amount"] or "",
            d["resolved_date"] or "",
            d["created_at"][:10] if d["created_at"] else ""
        ])

    output.seek(0)
    filename = f"pay_disputes_export_{datetime.now().strftime('%Y-%m-%d')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/api/pay-disputes/{dispute_id}")
async def get_single_pay_dispute(
    dispute_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pay_disputes", "view"))
):
    """Get single pay dispute"""
    dispute = get_pay_dispute_by_id(db, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Pay dispute not found")

    return {
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
    }


@app.post("/api/pay-disputes")
async def create_new_pay_dispute(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pay_disputes", "create"))
):
    """Create a new pay dispute"""
    data = await request.json()

    dispute_data = PayDisputeCreate(
        employee_id=data["employee_id"],
        dispute_type=data["dispute_type"],
        pay_period=data["pay_period"],
        disputed_amount=data.get("disputed_amount"),
        subject=data["subject"],
        description=data["description"],
        supporting_docs=data.get("supporting_docs"),
        priority=data.get("priority", "Medium")
    )

    dispute = create_pay_dispute(db, dispute_data, user.id)
    return {"status": "success", "id": dispute.id, "ticket_no": dispute.ticket_no}


@app.put("/api/pay-disputes/{dispute_id}")
async def update_pay_dispute_record(
    dispute_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pay_disputes", "edit"))
):
    """Update a pay dispute"""
    from datetime import datetime

    data = await request.json()

    # Parse resolved_date if present
    if data.get("resolved_date"):
        data["resolved_date"] = datetime.strptime(data["resolved_date"], "%Y-%m-%d").date()

    update_data = PayDisputeUpdate(**data)
    dispute = update_pay_dispute(db, dispute_id, update_data)

    if not dispute:
        raise HTTPException(status_code=404, detail="Pay dispute not found")

    return {"status": "success"}


@app.delete("/api/pay-disputes/{dispute_id}")
async def delete_pay_dispute_record(
    dispute_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pay_disputes", "delete"))
):
    """Delete a pay dispute"""
    if not delete_pay_dispute(db, dispute_id):
        raise HTTPException(status_code=404, detail="Pay dispute not found")

    return {"status": "success"}


@app.get("/api/pay-disputes/{dispute_id}/comments")
async def get_dispute_comments(
    dispute_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pay_disputes", "view"))
):
    """Get comments for a pay dispute"""
    dispute = get_pay_dispute_by_id(db, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Pay dispute not found")

    comments = get_pay_dispute_comments(db, dispute_id, include_internal=True)
    return {"comments": comments}


@app.post("/api/pay-disputes/{dispute_id}/comments")
async def add_dispute_comment(
    dispute_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("pay_disputes", "edit"))
):
    """Add a comment to a pay dispute"""
    dispute = get_pay_dispute_by_id(db, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Pay dispute not found")

    data = await request.json()
    comment_data = PayDisputeCommentCreate(
        comment=data["comment"],
        is_internal=data.get("is_internal", False)
    )

    comment = add_pay_dispute_comment(db, dispute_id, user.id, comment_data)
    return {"status": "success", "id": comment.id}


# ============== IR/NTE Log API Endpoints ==============

@app.get("/api/ir-nte-logs")
async def get_ir_nte_logs_list(
    request: Request,
    search: str = None,
    doc_type: str = None,
    status: str = None,
    campaign: str = None,
    filed_date_from: str = None,
    filed_date_to: str = None,
    nte_date_from: str = None,
    nte_date_to: str = None,
    has_explanation: bool = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("ir_nte_logs", "view"))
):
    """Get IR/NTE logs with filtering and pagination"""
    from datetime import datetime

    filters = IRNTELogFilter(
        search=search,
        doc_type=doc_type,
        status=status,
        campaign=campaign,
        filed_date_from=datetime.strptime(filed_date_from, "%Y-%m-%d").date() if filed_date_from else None,
        filed_date_to=datetime.strptime(filed_date_to, "%Y-%m-%d").date() if filed_date_to else None,
        nte_date_from=datetime.strptime(nte_date_from, "%Y-%m-%d").date() if nte_date_from else None,
        nte_date_to=datetime.strptime(nte_date_to, "%Y-%m-%d").date() if nte_date_to else None,
        has_explanation=has_explanation,
        page=page,
        limit=limit
    )

    return get_ir_nte_logs(db, filters)


@app.get("/api/ir-nte-logs/statistics")
async def get_ir_nte_stats(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("ir_nte_logs", "view"))
):
    """Get IR/NTE log statistics"""
    return get_ir_nte_statistics(db)


@app.get("/api/ir-nte-logs/filter-options")
async def get_ir_nte_filters(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("ir_nte_logs", "view"))
):
    """Get unique values for IR/NTE log filters"""
    return get_ir_nte_filter_options(db)


@app.get("/api/ir-nte-logs/export")
async def export_ir_nte_logs_csv(
    request: Request,
    search: str = None,
    doc_type: str = None,
    status: str = None,
    campaign: str = None,
    filed_date_from: str = None,
    filed_date_to: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("ir_nte_logs", "view"))
):
    """Export IR/NTE logs to CSV"""
    from datetime import datetime
    import csv
    import io

    filters = IRNTELogFilter(
        search=search,
        doc_type=doc_type,
        status=status,
        campaign=campaign,
        filed_date_from=datetime.strptime(filed_date_from, "%Y-%m-%d").date() if filed_date_from else None,
        filed_date_to=datetime.strptime(filed_date_to, "%Y-%m-%d").date() if filed_date_to else None,
        page=1,
        limit=100000
    )

    result = get_ir_nte_logs(db, filters)
    logs = result["logs"]

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Doc ID", "Type", "Employee No", "Employee Name", "Campaign",
        "Filed Date", "Complaint/Violation", "Received Date", "NTE Date",
        "Has Explanation", "Status", "Resolution", "Remarks"
    ])

    for log in logs:
        writer.writerow([
            log["doc_id"],
            log["doc_type"],
            log["employee_no"],
            log["employee_name"],
            log["campaign"],
            log["filed_date"],
            log["complaint_violation"],
            log["received_date"] or "",
            log["nte_date"] or "",
            "Yes" if log["has_explanation"] else "No",
            log["status"],
            log["resolution"] or "",
            log["remarks"] or ""
        ])

    output.seek(0)
    filename = f"ir_nte_logs_export_{datetime.now().strftime('%Y-%m-%d')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/api/ir-nte-logs/{log_id}")
async def get_single_ir_nte_log(
    log_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("ir_nte_logs", "view"))
):
    """Get single IR/NTE log"""
    log = get_ir_nte_by_id(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="IR/NTE log not found")

    return {
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
    }


@app.post("/api/ir-nte-logs")
async def create_new_ir_nte_log(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("ir_nte_logs", "create"))
):
    """Create a new IR/NTE log"""
    from datetime import datetime

    data = await request.json()

    log_data = IRNTELogCreate(
        employee_id=data["employee_id"],
        doc_type=data["doc_type"],
        filed_date=datetime.strptime(data["filed_date"], "%Y-%m-%d").date(),
        complaint_violation=data["complaint_violation"],
        received_date=datetime.strptime(data["received_date"], "%Y-%m-%d").date() if data.get("received_date") else None,
        nte_date=datetime.strptime(data["nte_date"], "%Y-%m-%d").date() if data.get("nte_date") else None,
        attachment_path=data.get("attachment_path"),
        nte_form_path=data.get("nte_form_path"),
        remarks=data.get("remarks")
    )

    log = create_ir_nte_log(db, log_data, user.id)
    return {"status": "success", "id": log.id, "doc_id": log.doc_id}


@app.put("/api/ir-nte-logs/{log_id}")
async def update_ir_nte_log_record(
    log_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("ir_nte_logs", "edit"))
):
    """Update an IR/NTE log"""
    from datetime import datetime

    data = await request.json()

    # Parse date fields if present
    date_fields = ["filed_date", "received_date", "nte_date", "explanation_date", "resolution_date"]
    for field in date_fields:
        if data.get(field):
            data[field] = datetime.strptime(data[field], "%Y-%m-%d").date()

    update_data = IRNTELogUpdate(**data)
    log = update_ir_nte_log(db, log_id, update_data)

    if not log:
        raise HTTPException(status_code=404, detail="IR/NTE log not found")

    return {"status": "success"}


@app.delete("/api/ir-nte-logs/{log_id}")
async def delete_ir_nte_log_record(
    log_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("ir_nte_logs", "delete"))
):
    """Delete an IR/NTE log"""
    if not delete_ir_nte_log(db, log_id):
        raise HTTPException(status_code=404, detail="IR/NTE log not found")

    return {"status": "success"}


# ============== Startup Events ==============

@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    try:
        # Seed roles and modules
        seed_roles_and_modules(db)
        print("Roles and modules seeded successfully")

        # Create default admin user with admin role
        existing = get_user_by_email(db, "admin@bpo.com")
        admin_role = get_role_by_name(db, "admin")

        if not existing and admin_role:
            admin_user = create_user(
                db=db,
                email="admin@bpo.com",
                password="admin123",
                full_name="System Administrator",
                employee_no="E001",
                role_id=admin_role.id
            )
            print("Default admin user created: admin@bpo.com / admin123")
        elif existing and admin_role and not existing.role_id:
            existing.role_id = admin_role.id
            db.commit()
            print("Admin role assigned to existing admin user")
        
        # Seed employees if needed
        existing_employees = db.query(User).filter(User.employee_no != "E001").count()
        if existing_employees < 250:
            print("Seeding 250 employees...")
            from scripts.seed_employees import seed_employees
            seed_employees(db)
        else:
            print(f"Database already has {existing_employees} employees")

        # Seed shift schedules if needed
        try:
            from scripts.seed_schedules import seed_schedules
            seed_schedules(db)
        except Exception as e:
            print(f"Note: Schedule seeding skipped or error occurred: {e}")

        # Seed DTR records if needed
        try:
            from scripts.seed_dtr import seed_dtr
            seed_dtr(db)
        except Exception as e:
            print(f"Note: DTR seeding skipped or error occurred: {e}")

        # Seed pay disputes if needed
        try:
            from scripts.seed_pay_disputes import seed_pay_disputes
            seed_pay_disputes(db)
        except Exception as e:
            print(f"Note: Pay disputes seeding skipped or error occurred: {e}")
    finally:
        db.close()
