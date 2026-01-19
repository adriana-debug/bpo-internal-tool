from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from app.models.user import User
from app.models.rbac import Role, Module, RoleModulePermission, UserModulePermission


# Module definitions with categories
MODULES = [
    # Operations
    {"name": "dashboard", "display_name": "Dashboard", "category": "dashboard", "icon": "solar:pie-chart-2-bold-duotone", "route": "/dashboard", "sort_order": 0},
    {"name": "schedule", "display_name": "Schedule", "category": "operations", "icon": "solar:calendar-bold-duotone", "route": "/operations/schedule", "sort_order": 1},
    {"name": "dtr", "display_name": "Daily Time Record", "category": "operations", "icon": "solar:clock-circle-bold-duotone", "route": "/operations/dtr", "sort_order": 2},
    # HR & People
    {"name": "employee_directory", "display_name": "Employee Directory", "category": "operations", "icon": "solar:users-group-rounded-bold-duotone", "route": "/operations/employee-directory", "sort_order": 10},
    {"name": "requests", "display_name": "Requests", "category": "hr_people", "icon": "solar:clipboard-list-bold-duotone", "route": "/hr/requests", "sort_order": 11},
    {"name": "pay_disputes", "display_name": "Pay Disputes", "category": "hr_people", "icon": "solar:wallet-money-bold-duotone", "route": "/hr/pay-disputes", "sort_order": 12},
    {"name": "ir_nte_logs", "display_name": "IR/NTE Logs", "category": "hr_people", "icon": "solar:document-text-bold-duotone", "route": "/hr/ir-nte", "sort_order": 13},
    {"name": "onboarding", "display_name": "Onboarding", "category": "hr_people", "icon": "solar:user-plus-bold-duotone", "route": "/hr/onboarding", "sort_order": 14},
    # Admin
    {"name": "user_management", "display_name": "User Management", "category": "admin", "icon": "solar:users-group-two-rounded-bold-duotone", "route": "/admin/users", "sort_order": 90},
    {"name": "role_management", "display_name": "Role Management", "category": "admin", "icon": "solar:shield-user-bold-duotone", "route": "/admin/roles", "sort_order": 91},
    {"name": "system_settings", "display_name": "System Settings", "category": "admin", "icon": "solar:settings-bold-duotone", "route": "/admin/settings", "sort_order": 92},
]

# Role definitions with default module access
ROLES = [
    {
        "name": "admin",
        "display_name": "Administrator",
        "description": "Full system access",
        "is_system_role": True,
        "permissions": {
            "dashboard": {"view": True, "create": True, "edit": True, "delete": True},
            "schedule": {"view": True, "create": True, "edit": True, "delete": True},
            "dtr": {"view": True, "create": True, "edit": True, "delete": True},
            "employee_directory": {"view": True, "create": True, "edit": True, "delete": True},
            "requests": {"view": True, "create": True, "edit": True, "delete": True},
            "pay_disputes": {"view": True, "create": True, "edit": True, "delete": True},
            "ir_nte_logs": {"view": True, "create": True, "edit": True, "delete": True},
            "onboarding": {"view": True, "create": True, "edit": True, "delete": True},
            "user_management": {"view": True, "create": True, "edit": True, "delete": True},
            "role_management": {"view": True, "create": True, "edit": True, "delete": True},
            "system_settings": {"view": True, "create": True, "edit": True, "delete": True},
        }
    },
    {
        "name": "executive",
        "display_name": "Executive",
        "description": "Executive level access - view all, limited edit",
        "is_system_role": True,
        "permissions": {
            "dashboard": {"view": True, "create": False, "edit": False, "delete": False},
            "schedule": {"view": True, "create": False, "edit": False, "delete": False},
            "dtr": {"view": True, "create": False, "edit": False, "delete": False},
            "employee_directory": {"view": True, "create": False, "edit": False, "delete": False},
            "requests": {"view": True, "create": False, "edit": True, "delete": False},
            "pay_disputes": {"view": True, "create": False, "edit": False, "delete": False},
            "ir_nte_logs": {"view": True, "create": False, "edit": False, "delete": False},
            "onboarding": {"view": True, "create": False, "edit": False, "delete": False},
        }
    },
    {
        "name": "human_resource",
        "display_name": "Human Resource",
        "description": "Full HR & People module access",
        "is_system_role": True,
        "permissions": {
            "dashboard": {"view": True, "create": False, "edit": False, "delete": False},
            "employee_directory": {"view": True, "create": True, "edit": True, "delete": True},
            "requests": {"view": True, "create": True, "edit": True, "delete": True},
            "pay_disputes": {"view": True, "create": True, "edit": True, "delete": True},
            "ir_nte_logs": {"view": True, "create": True, "edit": True, "delete": True},
            "onboarding": {"view": True, "create": True, "edit": True, "delete": True},
        }
    },
    {
        "name": "finance",
        "display_name": "Finance",
        "description": "Finance and payroll access",
        "is_system_role": True,
        "permissions": {
            "dashboard": {"view": True, "create": False, "edit": False, "delete": False},
            "employee_directory": {"view": True, "create": False, "edit": False, "delete": False},
            "pay_disputes": {"view": True, "create": True, "edit": True, "delete": False},
            "dtr": {"view": True, "create": False, "edit": False, "delete": False},
        }
    },
    {
        "name": "it",
        "display_name": "IT",
        "description": "IT and system administration",
        "is_system_role": True,
        "permissions": {
            "dashboard": {"view": True, "create": False, "edit": False, "delete": False},
            "user_management": {"view": True, "create": True, "edit": True, "delete": False},
            "system_settings": {"view": True, "create": False, "edit": True, "delete": False},
            "employee_directory": {"view": True, "create": False, "edit": False, "delete": False},
        }
    },
    {
        "name": "project_manager",
        "display_name": "Project Manager",
        "description": "Project and team management",
        "is_system_role": True,
        "permissions": {
            "dashboard": {"view": True, "create": False, "edit": False, "delete": False},
            "schedule": {"view": True, "create": True, "edit": True, "delete": False},
            "dtr": {"view": True, "create": False, "edit": False, "delete": False},
            "employee_directory": {"view": True, "create": False, "edit": False, "delete": False},
            "requests": {"view": True, "create": False, "edit": True, "delete": False},
        }
    },
    {
        "name": "supervisor",
        "display_name": "Supervisor",
        "description": "Team supervisor - operations focus",
        "is_system_role": True,
        "permissions": {
            "dashboard": {"view": True, "create": False, "edit": False, "delete": False},
            "schedule": {"view": True, "create": True, "edit": True, "delete": False},
            "dtr": {"view": True, "create": True, "edit": True, "delete": False},
            "employee_directory": {"view": True, "create": False, "edit": False, "delete": False},
            "requests": {"view": True, "create": True, "edit": True, "delete": False},
            "ir_nte_logs": {"view": True, "create": True, "edit": True, "delete": False},
        }
    },
    {
        "name": "manager",
        "display_name": "Manager",
        "description": "Operations manager - full operations access",
        "is_system_role": True,
        "permissions": {
            "dashboard": {"view": True, "create": False, "edit": False, "delete": False},
            "schedule": {"view": True, "create": True, "edit": True, "delete": True},
            "dtr": {"view": True, "create": True, "edit": True, "delete": True},
            "employee_directory": {"view": True, "create": False, "edit": True, "delete": False},
            "requests": {"view": True, "create": True, "edit": True, "delete": True},
            "ir_nte_logs": {"view": True, "create": True, "edit": True, "delete": False},
        }
    },
    {
        "name": "agent",
        "display_name": "Agent",
        "description": "Regular employee - basic access",
        "is_system_role": True,
        "permissions": {
            "dashboard": {"view": True, "create": False, "edit": False, "delete": False},
            "dtr": {"view": True, "create": True, "edit": False, "delete": False},
            "requests": {"view": True, "create": True, "edit": False, "delete": False},
        }
    },
]


def seed_roles_and_modules(db: Session):
    """Initialize roles and modules in database"""
    # Create modules
    for mod_data in MODULES:
        existing = db.query(Module).filter(Module.name == mod_data["name"]).first()
        if not existing:
            module = Module(**mod_data)
            db.add(module)
    db.commit()

    # Create roles with permissions
    for role_data in ROLES:
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing_role:
            role = Role(
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                is_system_role=role_data["is_system_role"]
            )
            db.add(role)
            db.commit()
            db.refresh(role)

            # Add permissions
            for module_name, perms in role_data.get("permissions", {}).items():
                module = db.query(Module).filter(Module.name == module_name).first()
                if module:
                    permission = RoleModulePermission(
                        role_id=role.id,
                        module_id=module.id,
                        can_view=perms.get("view", False),
                        can_create=perms.get("create", False),
                        can_edit=perms.get("edit", False),
                        can_delete=perms.get("delete", False)
                    )
                    db.add(permission)
            db.commit()


def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    return db.query(Role).filter(Role.name == name).first()


def get_all_roles(db: Session) -> List[Role]:
    return db.query(Role).all()


def get_user_permissions(db: Session, user: User) -> Dict[str, Dict[str, bool]]:
    """
    Get combined permissions for a user (role permissions + custom permissions).
    Custom permissions override role permissions.
    """
    permissions = {}

    # Get role permissions
    if user.role:
        role_perms = db.query(RoleModulePermission).filter(
            RoleModulePermission.role_id == user.role_id
        ).all()
        for perm in role_perms:
            module = db.query(Module).filter(Module.id == perm.module_id).first()
            if module:
                permissions[module.name] = {
                    "view": perm.can_view,
                    "create": perm.can_create,
                    "edit": perm.can_edit,
                    "delete": perm.can_delete,
                    "module": module
                }

    # Override with custom permissions (cross-functional clearance)
    custom_perms = db.query(UserModulePermission).filter(
        UserModulePermission.user_id == user.id
    ).all()
    for perm in custom_perms:
        module = db.query(Module).filter(Module.id == perm.module_id).first()
        if module:
            if module.name not in permissions:
                permissions[module.name] = {"module": module}
            # Custom permissions add to existing (OR logic)
            permissions[module.name]["view"] = permissions[module.name].get("view", False) or perm.can_view
            permissions[module.name]["create"] = permissions[module.name].get("create", False) or perm.can_create
            permissions[module.name]["edit"] = permissions[module.name].get("edit", False) or perm.can_edit
            permissions[module.name]["delete"] = permissions[module.name].get("delete", False) or perm.can_delete

    return permissions


def get_accessible_modules(db: Session, user: User) -> List[Dict]:
    """Get list of modules user can access (view permission)"""
    permissions = get_user_permissions(db, user)
    accessible = []

    all_modules = db.query(Module).filter(Module.is_active == True).order_by(Module.sort_order).all()
    for module in all_modules:
        if module.name in permissions and permissions[module.name].get("view", False):
            accessible.append({
                "name": module.name,
                "display_name": module.display_name,
                "category": module.category,
                "icon": module.icon,
                "route": module.route,
                "can_view": permissions[module.name].get("view", False),
                "can_create": permissions[module.name].get("create", False),
                "can_edit": permissions[module.name].get("edit", False),
                "can_delete": permissions[module.name].get("delete", False),
            })

    return accessible


def check_permission(db: Session, user: User, module_name: str, action: str = "view") -> bool:
    """Check if user has specific permission on a module"""
    permissions = get_user_permissions(db, user)
    if module_name not in permissions:
        return False
    return permissions[module_name].get(action, False)


def grant_custom_permission(
    db: Session,
    user_id: int,
    module_name: str,
    can_view: bool = False,
    can_create: bool = False,
    can_edit: bool = False,
    can_delete: bool = False,
    granted_by: int = None
) -> UserModulePermission:
    """Grant custom module access to a user (cross-functional clearance)"""
    module = db.query(Module).filter(Module.name == module_name).first()
    if not module:
        raise ValueError(f"Module {module_name} not found")

    # Check if custom permission already exists
    existing = db.query(UserModulePermission).filter(
        UserModulePermission.user_id == user_id,
        UserModulePermission.module_id == module.id
    ).first()

    if existing:
        existing.can_view = can_view
        existing.can_create = can_create
        existing.can_edit = can_edit
        existing.can_delete = can_delete
        existing.granted_by = granted_by
    else:
        existing = UserModulePermission(
            user_id=user_id,
            module_id=module.id,
            can_view=can_view,
            can_create=can_create,
            can_edit=can_edit,
            can_delete=can_delete,
            granted_by=granted_by
        )
        db.add(existing)

    db.commit()
    db.refresh(existing)
    return existing


def revoke_custom_permission(db: Session, user_id: int, module_name: str) -> bool:
    """Revoke custom module access from a user"""
    module = db.query(Module).filter(Module.name == module_name).first()
    if not module:
        return False

    perm = db.query(UserModulePermission).filter(
        UserModulePermission.user_id == user_id,
        UserModulePermission.module_id == module.id
    ).first()

    if perm:
        db.delete(perm)
        db.commit()
        return True
    return False
