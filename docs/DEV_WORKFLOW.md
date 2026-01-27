# Development Workflow

## Quick Reference

| Task | Command |
|------|---------|
| Start dev (Docker) | `docker-compose up --build` |
| Start dev (local) | `python run_server.py` |
| Stop Docker | `docker-compose down` |
| Run tests | `pytest tests/` |
| Reset database | `python scripts/reset_db.py` |
| Seed employees | `python scripts/seed_employees.py` |
| Seed schedules | `python scripts/seed_schedules.py` |
| Seed DTR | `python scripts/seed_dtr.py` |
| View logs | `docker-compose logs -f web` |
| MySQL CLI | `docker exec -it bpo-mysql mysql -u bpo_user -p bpo_platform` |

---

## Development Server

### Docker Development (MySQL) - Recommended
```bash
docker-compose up --build
```
- MySQL 8.0 with health checks
- Data persisted in `mysql_data` volume
- App waits for DB to be healthy before starting
- Production-like environment

Server runs at http://localhost:8005

**Default Login:** `admin@bpo.com` / `admin123`

### Local Development (without Docker)
```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Start server with hot reload
python run_server.py
# OR
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```
Requires MySQL running locally or update `.env` to use SQLite for quick testing.

---

## Frontend Development

### File Locations
```
app/
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Base layout (head, scripts, theme)
│   ├── login.html          # Login page
│   ├── dashboard.html      # Main dashboard with KPIs
│   ├── admin/
│   │   ├── users.html      # User management
│   │   └── roles.html      # Role management
│   ├── operations/
│   │   ├── employee-directory.html
│   │   ├── shift-schedule.html
│   │   └── dtr.html
│   └── components/
│       └── sidebar.html    # Navigation sidebar
└── static/
    ├── css/
    │   ├── themes.css      # Theme colors & dark mode
    │   └── theme-selector.css
    └── js/
        ├── theme-manager.js
        └── employee-directory.js
```

### Template System
- Templates use **Jinja2** syntax
- Extend `base.html` for consistent layout
- Components in `components/` are reusable partials

### Template Variables
Routes pass data to templates:
```python
return templates.TemplateResponse("page.html", {
    "request": request,      # Required by Jinja2
    "user": user,            # Current logged-in user
    "modules": modules,      # Accessible modules for sidebar
    "current_route": "/path" # For active nav highlighting
})
```

### Styling
- **TailwindCSS** via CDN
- **Iconify** for icons (Solar icon set)
- Custom theme colors in `themes.css`
- Dark mode support built-in

---

## Backend Development

### File Structure
```
app/
├── main.py                 # FastAPI app, all routes
├── core/
│   ├── config.py           # Settings from .env
│   ├── database.py         # SQLAlchemy engine/session
│   └── security.py         # JWT, password hashing
├── models/
│   ├── user.py             # User, ShiftSchedule models
│   ├── rbac.py             # Role, Module, Permission models
│   └── requests.py         # Requests model (NEW)
├── schemas/
│   ├── auth.py             # Login schemas
│   ├── employee.py         # Employee CRUD schemas
│   ├── shift_schedule.py   # Schedule schemas
│   ├── dtr.py              # DTR schemas
│   └── requests.py         # Requests schemas (NEW)
└── services/
    ├── auth_service.py     # Authentication logic
    ├── employee_service.py # Employee CRUD operations
    ├── rbac_service.py     # Role/permission management
    ├── shift_schedule_service.py
    ├── dtr_service.py      # DTR operations
    └── requests_service.py # Requests logic (NEW)
```
### Requests Feature (NEW)

#### Adding a Request
1. **Model:** Define in `app/models/requests.py` (see example below)
2. **Schema:** Add Pydantic schemas in `app/schemas/requests.py`
3. **Service:** Implement CRUD logic in `app/services/requests_service.py`
4. **API & Page Route:** Add endpoints and page in `app/main.py`
5. **Template:** Create `app/templates/operations/requests.html`

**Example SQLAlchemy Model:**
```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from app.core.database import Base
from datetime import datetime

class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Example Pydantic Schema:**
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RequestCreate(BaseModel):
    type: str
    details: Optional[str] = None

class RequestOut(BaseModel):
    id: int
    user_id: int
    type: str
    status: str
    details: Optional[str]
    created_at: datetime
    class Config:
        orm_mode = True
```

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/api/requests` | List requests |
| POST   | `/api/requests` | Create request |
| GET    | `/api/requests/{id}` | Get request |
| PUT    | `/api/requests/{id}` | Update request |
| DELETE | `/api/requests/{id}` | Delete request |

**Page Route:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/operations/requests` | Requests page view |

**Template:**
Create `app/templates/operations/requests.html` extending `base.html` and listing requests.

**Testing:**
Add tests in `tests/test_requests.py` for API and page.

### Adding a New Page Route

1. **Create template** in `app/templates/`

2. **Add route** in `app/main.py`:
```python
@app.get("/my-page", response_class=HTMLResponse)
async def my_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("module_name", "view"))
):
    modules = get_accessible_modules(db, user)
    return templates.TemplateResponse("my-page.html", {
        "request": request,
        "user": user,
        "modules": modules,
        "current_route": "/my-page"
    })
```

### Adding an API Endpoint

1. **Define schema** in `app/schemas/`:
```python
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str
    value: int
```

2. **Add endpoint** in `app/main.py`:
```python
@app.post("/api/items")
async def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("module", "create"))
):
    # Implementation
    return {"status": "success", "id": new_id}
```

3. **Add service function** (optional, for complex logic) in `app/services/`

### Permission System

Routes use `require_permission(module, action)` dependency:
```python
# Actions: "view", "create", "edit", "delete"
user: User = Depends(require_permission("employee_directory", "edit"))
```

This checks:
1. User's role default permissions
2. User's custom permission overrides (cross-functional access)

---

## Database Development

### Models

**User** (`app/models/user.py`):
- `id`, `employee_no`, `email`, `hashed_password`, `full_name`
- `role_id`, `campaign`, `department`
- `date_of_joining`, `last_working_date`, `tenure_months`
- `employee_status` (Active/Inactive/Transfer)
- `is_active`, `created_at`, `updated_at`

#### Seeded Employee Campaign Distribution (Sample Data)

| Campaign    | Active | Inactive | Transfer | Total |
|-------------|--------|----------|----------|-------|
| Campaign 1  |   1    |    2     |    0     |   3   |
| Campaign 2  |   2    |    0     |    0     |   2   |
| Campaign 3  |   2    |    0     |    0     |   2   |
| Campaign 4  |   2    |    0     |    0     |   2   |
| Campaign 5  |   2    |    0     |    0     |   2   |
| Campaign 6  |   4    |    0     |    0     |   4   |
| Campaign 7  |   6    |    0     |    0     |   6   |
| Campaign 8  |   2    |    0     |    0     |   2   |
| Campaign 9  |   0    |    8     |    1     |   9   |
| Campaign 10 |   1    |    0     |    0     |   1   |
| Campaign 11 |   1    |    1     |    0     |   2   |
| **Total**   | **23** | **11**   | **1**    | **35**|

Each seeded employee is unique and realistic. The admin user (E001) is unchanged.

**ShiftSchedule** (`app/models/user.py`):
- `id`, `user_id`, `schedule_date`, `day_of_week`
- `shift_time`, `shift_start`, `shift_end`
- `campaign`, `notes`, `is_published`

**DailyTimeRecord** (`app/models/user.py`):
- `id`, `user_id`, `date`, `scheduled_shift`
- `time_in`, `time_out`, `break_in`, `break_out`
- `total_hours`, `overtime_hours`
- `status` (Present/Late/Absent/Incomplete/On Leave/Rest Day)
- `remarks`, `is_manual_entry`, `created_at`, `updated_at`

**Role** (`app/models/rbac.py`):
- `id`, `name`, `display_name`, `description`, `is_system_role`

**Module** (`app/models/rbac.py`):
- `id`, `name`, `display_name`, `category`, `icon`, `route`, `sort_order`

**RoleModulePermission** / **UserModulePermission**:
- `can_view`, `can_create`, `can_edit`, `can_delete`

### Adding a New Model

1. Create in `app/models/`:
```python
from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base

class MyModel(Base):
    __tablename__ = "my_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
```

2. Import in `app/main.py` to register
3. Restart server - tables auto-create on startup

### Database Commands
```bash
# Reset everything
python scripts/reset_db.py

# Seed 250 test employees
python scripts/seed_employees.py

# Seed shift schedules
python scripts/seed_schedules.py

# Seed 3 months of DTR records
python scripts/seed_dtr.py
```

### Direct Database Access

**MySQL (Docker)**
```bash
# Connect to MySQL container
docker exec -it bpo-mysql mysql -u bpo_user -pbpo_password bpo_platform

# Example queries
SHOW TABLES;
DESCRIBE users;
SELECT employee_no, full_name, employee_status FROM users LIMIT 10;
```

**MySQL Workbench / DBeaver**
- Host: `localhost`
- Port: `3306`
- Database: `bpo_platform`
- User: `bpo_user`
- Password: `bpo_password`

---

## API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/login` | Login page |
| POST | `/login` | Submit login |
| GET | `/logout` | Logout user |
| GET | `/health` | Health check |

### Users API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/{id}` | Get user |
| POST | `/api/users` | Create user |
| PUT | `/api/users/{id}` | Update user |
| DELETE | `/api/users/{id}` | Delete user |
| PATCH | `/api/users/{id}/toggle-status` | Toggle active |
| POST | `/api/users/{id}/role` | Change role |
| POST | `/api/users/{id}/permissions` | Set custom permissions |
| DELETE | `/api/users/{id}/permissions/{module}` | Revoke permission |

### Employees API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/employees` | List (with filters) |
| GET | `/api/employees/{id}` | Get employee |
| POST | `/api/employees` | Create employee |
| PUT | `/api/employees/{id}` | Update employee |
| DELETE | `/api/employees/{id}` | Delete employee |
| POST | `/api/employees/bulk-status-update` | Bulk status change |
| GET | `/api/employees/statistics` | Get stats |
| GET | `/api/employees/filter-options` | Get filter values |
| GET | `/api/employees/assessments-due` | Due assessments |

### Shift Schedule API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/shift-schedule` | Get weekly schedule |
| POST | `/api/shift-schedule/save` | Save shift |
| POST | `/api/shift-schedule/publish` | Publish week |
| POST | `/api/shift-schedule/upload` | Bulk upload |

### DTR API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/operations/dtr` | DTR page view |
| GET | `/api/dtr` | List records (filters: campaign, date_from, date_to, shift, status) |
| GET | `/api/dtr/statistics` | Get KPI stats (total, present, late, overtime) |
| GET | `/api/dtr/filter-options` | Get dropdown values |
| GET | `/api/dtr/{id}` | Get single record |
| POST | `/api/dtr` | Create manual entry |
| PUT | `/api/dtr/{id}` | Update record |
| DELETE | `/api/dtr/{id}` | Delete record |
| POST | `/api/dtr/upload` | Bulk upload CSV/Excel |

---

## Testing

### Run Tests
```bash
# All tests
pytest tests/

# Specific file
pytest tests/test_auth.py

# Verbose
pytest tests/ -v

# With coverage
pytest tests/ --cov=app
```

### Test Structure
```
tests/
├── __init__.py
├── test_auth.py              # Authentication tests
├── test_api.py               # API endpoint tests
├── test_employee_directory.py
├── test_user_management.py
├── test_comprehensive.py     # Integration tests
└── ...
```

### Writing Tests
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_login():
    response = client.post("/login", data={
        "email": "admin@bpo.com",
        "password": "admin123"
    })
    assert response.status_code == 303
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | DB connection | `mysql+pymysql://bpo_user:bpo_password@db:3306/bpo_platform` |
| `SECRET_KEY` | JWT signing key | `dev-secret-key` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `30` |

---

## Git Workflow

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `refactor/description` - Code improvements

### Commit Format
```
feat: add employee export to CSV
fix: resolve login redirect loop
refactor: extract validation to service
docs: update API documentation
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8005 in use | `netstat -ano \| findstr :8005` then `taskkill /PID <pid> /F` |
| Database connection error | Check Docker is running: `docker ps` |
| Import errors | Check venv activated, run `pip install -r requirements.txt` |
| Template not updating | Hard refresh (Ctrl+Shift+R) |
| Permission denied | Check user role has required permission |

---

## Dev Log

| Date | Change | Notes |
|------|--------|-------|
| 2026-01-20 | DTR module implementation | Full CRUD, filters, 3-month seed data |
| 2026-01-19 | MySQL Docker support | Production-like environment |
| 2026-01-19 | Project reorganization | tests/, scripts/, docs/ |
| 2026-01-19 | Initial dockerization | Dockerfile, docker-compose |

<!-- Add new entries at the top -->
