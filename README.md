# BPO Internal Platform

Internal management platform for BPO operations with role-based access control, employee directory, and shift scheduling.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Frontend**: Jinja2 templates, TailwindCSS, Iconify
- **Database**: SQLite (dev) / MySQL (production)
- **Auth**: JWT with HTTP-only cookies

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for MySQL)

### Local Development

```bash
# Clone repository
git clone https://github.com/adriana-debug/bpo-internal-tool.git
cd bpo-internal-tool

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run development server
python run_server.py
```

Visit http://localhost:8005

**Default credentials**: `admin@bpo.com` / `admin123`

### Docker (MySQL)

```bash
docker-compose up --build
```

Starts MySQL 8.0 + FastAPI app with production-like setup.

## Documentation

- [Development Workflow](docs/DEV_WORKFLOW.md) - How to develop, test, and deploy
- [Product Requirements](docs/PRD.md) - Features, roadmap, and specifications

## Project Structure

```
bpo-internal-tool/
├── app/
│   ├── core/           # Config, database, security
│   ├── models/         # SQLAlchemy models (User, Role, Module)
│   ├── schemas/        # Pydantic validation schemas
│   ├── services/       # Business logic layer
│   ├── templates/      # Jinja2 HTML templates
│   ├── static/         # CSS, JS assets
│   └── main.py         # FastAPI app & all routes
├── docs/               # Documentation
│   ├── DEV_WORKFLOW.md # Development guide
│   └── PRD.md          # Product requirements
├── scripts/            # Utility scripts
│   ├── seed_employees.py
│   ├── seed_schedules.py
│   ├── seed_dtr.py
│   └── reset_db.py
├── tests/              # Test suite
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Features

### Implemented
- User authentication (JWT)
- Role-based access control (9 roles)
- Employee directory with CRUD, filtering, search
- Shift scheduling with bulk upload
- User management with permission overrides
- Dark mode & theme customization
- **DTR (Daily Time Record)** - Time tracking with:
  - Data table: Employee Name, Date, Scheduled Shift, Time In/Out, Break In/Out, Total Hours, Overtime, Status
  - Filters: Campaign, Date Range, Shift, Status
  - Visual status indicators (Present, Late, Absent, Incomplete, On Leave, Rest Day)
  - Manual entry and bulk upload support

### Planned
- Leave/OT requests
- Pay disputes
- Onboarding module

## Scripts

```bash
# Seed 250 test employees
python scripts/seed_employees.py

# Seed shift schedules
python scripts/seed_schedules.py

# Seed 3 months of DTR records
python scripts/seed_dtr.py

# Reset database
python scripts/reset_db.py
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection | `sqlite:///./bpo_platform.db` |
| `SECRET_KEY` | JWT signing key | (change in production) |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `30` |

## API Endpoints

| Category | Count | Base Path |
|----------|-------|-----------|
| Auth | 4 | `/login`, `/logout`, `/health` |
| Users | 8 | `/api/users` |
| Employees | 9 | `/api/employees` |
| Schedules | 4 | `/api/shift-schedule` |
| DTR | 8 | `/api/dtr` |

### DTR Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/operations/dtr` | DTR page view |
| GET | `/api/dtr` | List records with filters (campaign, date, shift, status) |
| GET | `/api/dtr/statistics` | Get KPI statistics |
| GET | `/api/dtr/filter-options` | Get dropdown filter values |
| GET | `/api/dtr/{id}` | Get single record |
| POST | `/api/dtr` | Create manual entry |
| PUT | `/api/dtr/{id}` | Update record |
| DELETE | `/api/dtr/{id}` | Delete record |
| POST | `/api/dtr/upload` | Bulk upload CSV/Excel |

See [DEV_WORKFLOW.md](docs/DEV_WORKFLOW.md) for full API reference.

## License

Proprietary - Internal use only
