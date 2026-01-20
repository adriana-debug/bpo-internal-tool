# Product Requirements Document (PRD)

## BPO Internal Platform

**Version**: 1.0.0
**Last Updated**: 2026-01-20
**Status**: In Development

---

## Overview

Internal management platform for BPO operations providing employee management, shift scheduling, and role-based access control.

**Tech Stack**: FastAPI, SQLAlchemy, Jinja2, TailwindCSS, MySQL/SQLite

---

## User Roles

| Role | Code | Description |
|------|------|-------------|
| Administrator | `admin` | Full system access |
| Executive | `executive` | View-only access to all modules |
| Human Resource | `human_resource` | Employee & HR module management |
| Finance | `finance` | Pay-related module access |
| IT | `it` | Technical/system access |
| Project Manager | `project_manager` | Project & team management |
| Supervisor | `supervisor` | Team scheduling & oversight |
| Manager | `manager` | Department management |
| Agent | `agent` | Self-service only |

---

## Module Status

### 1. Authentication & Security
| Feature | Status | API | Notes |
|---------|--------|-----|-------|
| Email/password login | Done | `POST /login` | JWT + httponly cookies |
| Logout | Done | `GET /logout` | Clears cookie |
| Password hashing | Done | - | bcrypt |
| Token expiration | Done | - | Configurable (default 30min) |
| Role-based access | Done | - | 9 roles with permissions |
| Module permissions | Done | - | View/Create/Edit/Delete |
| Custom user permissions | Done | - | Cross-functional access |
| Password reset | Planned | - | - |
| Session management | Planned | - | - |
| Audit logging | Planned | - | - |

### 2. Dashboard
| Feature | Status | Route | Notes |
|---------|--------|-------|-------|
| Main dashboard | Done | `/dashboard` | KPI cards, sidebar |
| Role-based navigation | Done | - | Shows accessible modules |
| Theme selector | Done | - | Multiple color themes |
| Dark mode | Done | - | Toggle in header |
| Live KPI widgets | Planned | - | Currently hardcoded data |
| Notifications | Planned | - | UI exists, no backend |
| Recent activity | Planned | - | - |

### 3. Employee Directory
| Feature | Status | API | Notes |
|---------|--------|-----|-------|
| Employee listing | Done | `GET /api/employees` | Paginated |
| Search | Done | `?search=` | Name, email, employee_no |
| Filter by campaign | Done | `?campaign=` | - |
| Filter by department | Done | `?department=` | - |
| Filter by status | Done | `?employee_status=` | 7 status types |
| Filter by role | Done | `?role_name=` | - |
| Sorting | Done | `?sort_by=&sort_order=` | - |
| Create employee | Done | `POST /api/employees` | - |
| Update employee | Done | `PUT /api/employees/{id}` | - |
| Delete employee | Done | `DELETE /api/employees/{id}` | - |
| Bulk status update | Done | `POST /api/employees/bulk-status-update` | - |
| Statistics | Done | `GET /api/employees/statistics` | Counts by status |
| Filter options | Done | `GET /api/employees/filter-options` | Unique values |
| Assessment tracking | Done | `GET /api/employees/assessments-due` | Due within X days |
| Tenure calculation | Done | - | Auto-calculated months |
| Export CSV | Planned | - | - |
| Import CSV | Planned | - | - |
| Employee photos | Planned | - | - |

### 4. Shift Schedule
| Feature | Status | API | Notes |
|---------|--------|-----|-------|
| Weekly schedule view | Done | `GET /api/shift-schedule` | - |
| Save individual shift | Done | `POST /api/shift-schedule/save` | - |
| Publish schedule | Done | `POST /api/shift-schedule/publish` | Week-based |
| Bulk upload | Done | `POST /api/shift-schedule/upload` | - |
| Filter by campaign | Done | `?campaign=` | - |
| Filter by shift | Done | `?shift=` | - |
| Search employees | Done | `?search=` | - |
| Shift time parsing | Done | - | "9am to 5pm" format |
| Calendar view | Planned | - | - |
| Shift swap requests | Planned | - | - |
| Schedule notifications | Planned | - | - |

### 5. User Management (Admin)
| Feature | Status | API | Notes |
|---------|--------|-----|-------|
| User listing | Done | Page: `/admin/users` | - |
| Create user | Done | `POST /api/users` | - |
| Update user | Done | `PUT /api/users/{id}` | - |
| Delete user | Done | `DELETE /api/users/{id}` | Protected: can't self-delete |
| Toggle status | Done | `PATCH /api/users/{id}/toggle-status` | - |
| Change role | Done | `POST /api/users/{id}/role` | - |
| Custom permissions | Done | `POST /api/users/{id}/permissions` | Grant cross-functional |
| Revoke permissions | Done | `DELETE /api/users/{id}/permissions/{module}` | - |
| User statistics | Done | - | Active/inactive counts |
| Bulk actions | Planned | - | - |

### 6. Role Management (Admin)
| Feature | Status | Route | Notes |
|---------|--------|-------|-------|
| Role listing | Done | `/admin/roles` | 9 system roles |
| View permissions | Done | - | Per-module breakdown |
| System role protection | Done | - | Cannot delete system roles |
| Custom role creation | Planned | - | - |
| Edit role permissions | Planned | - | - |

---

### 7. Daily Time Record (DTR)
| Feature | Status | API | Notes |
|---------|--------|-----|-------|
| DTR page view | Done | `GET /operations/dtr` | Data table with filters |
| DTR listing | Done | `GET /api/dtr` | Paginated, filterable |
| Filter by campaign | Done | `?campaign=` | Dropdown filter |
| Filter by date range | Done | `?date_from=&date_to=` | Date picker |
| Filter by shift | Done | `?shift=` | Dropdown filter |
| Filter by status | Done | `?status=` | 6 status types |
| Search employees | Done | `?search=` | Name, employee_no |
| KPI statistics | Done | `GET /api/dtr/statistics` | Total, present, late, overtime |
| Filter options | Done | `GET /api/dtr/filter-options` | Dropdown values |
| Get single record | Done | `GET /api/dtr/{id}` | - |
| Manual entry | Done | `POST /api/dtr` | Add/edit modal |
| Update record | Done | `PUT /api/dtr/{id}` | - |
| Delete record | Done | `DELETE /api/dtr/{id}` | - |
| Bulk upload | Done | `POST /api/dtr/upload` | CSV/Excel support |
| Status indicators | Done | - | Color-coded badges |
| 3-month seed data | Done | `seed_dtr.py` | ~15,000 records |
| Biometric integration | Planned | - | External system |
| Export to Excel | Planned | - | - |

---

## Planned Modules (Not Implemented)

### 8. Requests Management
| Feature | Status | Notes |
|---------|--------|-------|
| Leave requests | Planned | Module defined |
| OT requests | Planned | - |
| Approval workflow | Planned | - |

### 9. Pay Disputes
| Feature | Status | Notes |
|---------|--------|-------|
| Dispute submission | Planned | Module defined |
| Case tracking | Planned | - |
| Resolution workflow | Planned | - |

### 10. IR/NTE Logs
| Feature | Status | Notes |
|---------|--------|-------|
| Incident reports | Planned | Module defined |
| NTE issuance | Planned | - |
| Case management | Planned | - |

### 11. Onboarding
| Feature | Status | Notes |
|---------|--------|-------|
| Onboarding checklist | Planned | Module defined |
| Document submission | Planned | - |
| Training tracking | Planned | - |

### 12. System Settings
| Feature | Status | Notes |
|---------|--------|-------|
| Company settings | Planned | Module defined |
| Email configuration | Planned | - |
| Backup/restore | Planned | - |

---

## Technical Requirements

### Performance
- [ ] Page load < 2 seconds
- [ ] API response < 500ms
- [ ] Support 100+ concurrent users

### Security
- [x] JWT authentication (httponly cookies)
- [x] Password hashing (bcrypt)
- [x] Role-based access control
- [x] SQL injection prevention (SQLAlchemy ORM)
- [ ] Rate limiting
- [ ] CSRF protection
- [ ] Input sanitization audit

### Infrastructure
- [x] Docker containerization
- [x] MySQL support (docker-compose)
- [x] SQLite for local dev
- [x] Health check endpoint
- [ ] Redis caching
- [ ] Horizontal scaling

---

## Database Schema

### Core Tables
| Table | Description |
|-------|-------------|
| `users` | Employee/user accounts |
| `roles` | System roles (9 predefined) |
| `modules` | System modules (11 defined) |
| `role_module_permissions` | Default role permissions |
| `user_module_permissions` | Custom user overrides |
| `shift_schedules` | Employee shift assignments |
| `daily_time_records` | DTR entries (time in/out, breaks, status) |

### Employee Status Values
- Active
- Inactive
- Terminated
- On Leave
- Probation
- New Hire
- Resignation Pending

### Module Categories
- `dashboard` - Dashboard
- `operations` - Schedule, DTR
- `hr_people` - Employee Directory, Requests, Pay Disputes, IR/NTE, Onboarding
- `admin` - User Management, Role Management, System Settings

---

## API Summary

| Category | Endpoints | Auth Required |
|----------|-----------|---------------|
| Auth | 4 | No (login only) |
| Users | 8 | Yes + permission |
| Employees | 9 | Yes + permission |
| Schedules | 4 | Yes + permission |
| DTR | 9 | Yes + permission |
| **Total** | **34** | - |

---

## Changelog

### v1.1.0 (2026-01-20)
- DTR module with full CRUD operations
- DTR data table with Employee Name, Date, Shift, Time In/Out, Break In/Out, Hours, Overtime, Status
- DTR filters: Campaign, Date Range, Shift, Status
- DTR statistics/KPI cards
- Manual entry and bulk upload support
- Visual status indicators (Present, Late, Absent, Incomplete, On Leave, Rest Day)
- 3-month DTR seed data (~15,000 records)

### v1.0.0 (2026-01-19)
- Initial release
- Authentication with JWT
- Employee directory with full CRUD
- Shift scheduling
- User management with RBAC
- 9 predefined roles
- Docker + MySQL support

---

## Backlog

### High Priority
- [ ] Password reset functionality
- [ ] Export to CSV/Excel
- [ ] Dashboard live metrics (replace hardcoded)
- [x] ~~DTR module implementation~~ (Done v1.1.0)

### Medium Priority
- [ ] Email notifications
- [ ] Audit logging
- [ ] Calendar view for schedules
- [ ] Bulk user import

### Low Priority
- [ ] API documentation (Swagger UI)
- [ ] Mobile app considerations
- [ ] Localization support
- [ ] Dark mode refinements

---

## Notes

### Architecture Decisions
- **Monolithic**: All routes in `main.py` for simplicity
- **Jinja2 templates**: Server-side rendering, no SPA
- **SQLAlchemy ORM**: Database abstraction
- **JWT in cookies**: More secure than localStorage

### Known Limitations
- Dashboard KPIs use sample data
- No file upload for employee photos
- Bulk upload needs CSV format documentation
- DTR not integrated with biometric systems (manual entry only)

---

<!-- Update this document as features are implemented -->
