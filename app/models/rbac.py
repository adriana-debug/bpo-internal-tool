from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.core.database import Base

# Association table for Role <-> Module default access
role_module_access = Table(
    'role_module_access',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('module_id', Integer, ForeignKey('modules.id'), primary_key=True),
    Column('can_view', Boolean, default=True),
    Column('can_create', Boolean, default=False),
    Column('can_edit', Boolean, default=False),
    Column('can_delete', Boolean, default=False),
)

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)  # admin, executive, hr, etc.
    display_name = Column(String(100))
    description = Column(String(255), nullable=True)
    is_system_role = Column(Boolean, default=False)  # Cannot be deleted

    users = relationship("User", back_populates="role")
    module_permissions = relationship("RoleModulePermission", back_populates="role", cascade="all, delete-orphan")


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)  # employee_directory, schedule, etc.
    display_name = Column(String(100))
    description = Column(String(255), nullable=True)
    category = Column(String(50))  # operations, hr_people, admin
    icon = Column(String(100), nullable=True)
    route = Column(String(100), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    role_permissions = relationship("RoleModulePermission", back_populates="module", cascade="all, delete-orphan")
    user_permissions = relationship("UserModulePermission", back_populates="module", cascade="all, delete-orphan")


class RoleModulePermission(Base):
    """Default permissions for a role on a module"""
    __tablename__ = "role_module_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)
    can_view = Column(Boolean, default=False)
    can_create = Column(Boolean, default=False)
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)

    role = relationship("Role", back_populates="module_permissions")
    module = relationship("Module", back_populates="role_permissions")


class UserModulePermission(Base):
    """Custom per-user permissions (cross-functional clearance)"""
    __tablename__ = "user_module_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)
    can_view = Column(Boolean, default=False)
    can_create = Column(Boolean, default=False)
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    granted_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="custom_permissions")
    module = relationship("Module", back_populates="user_permissions")
