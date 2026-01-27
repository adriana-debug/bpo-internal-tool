#!/usr/bin/env python3
"""
Seed database with exactly 250 employees distributed across 80+ campaigns (2-3 per campaign).

Global Role Distribution (not per campaign):
- 10 Supervisors
- 1 Manager
- 3 Human Resources
- 1 Finance
- 2 IT
- 233 Agents (remaining)

Departments: Operations, Customer Service, Technical Support, Sales, QA, Training, HR, Finance, IT Support, Back Office, Collections, Retention

Statuses: Active (60%), Inactive (10%), On Leave (5%), Terminated (5%), New Hire (10%), Probation (10%)

Total: 250 employees across 80+ campaigns (2-3 employees per campaign)
"""

import random
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.user import User
from app.models.rbac import Role
from app.core.security import get_password_hash

# Global role quota distribution (role names must match RBAC service)
ROLE_QUOTAS = {
    "supervisor": 10,         # 10 Supervisors
    "manager": 1,             # 1 Manager
    "human_resource": 3,      # 3 Human Resources
    "finance": 1,             # 1 Finance
    "it": 2,                  # 2 IT
    "agent": 233,             # 233 Operations (remaining)
}

# Total employees to seed
TOTAL_EMPLOYEES = 250

# Employee statuses for random mixing (includes New Hire for recent hires)
EMPLOYEE_STATUSES = ["Active", "Inactive", "On Leave", "Terminated", "New Hire", "Probation"]

# Departments for variety
DEPARTMENTS = [
    "Operations", "Customer Service", "Technical Support", "Sales",
    "Quality Assurance", "Training", "Human Resources", "Finance",
    "IT Support", "Back Office", "Collections", "Retention"
]

FIRST_NAMES = [
    "John", "Jane", "Michael", "Patricia", "Robert", "Linda", "James", "Mary",
    "William", "Jennifer", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Betty",
    "Matthew", "Margaret", "Anthony", "Sandra", "Mark", "Ashley", "Donald", "Kimberly",
    "Steven", "Emily", "Paul", "Donna", "Andrew", "Michelle", "Joshua", "Dorothy",
    "Kenneth", "Carol", "Kevin", "Amanda", "Brian", "Melissa", "Edward", "Deborah",
    "Ronald", "Stephanie", "Anthony", "Rebecca", "Frank", "Sharon", "Ryan", "Laura",
    "Jose", "Cynthia", "Larry", "Kathleen", "Justin", "Amy", "Scott", "Angela",
    "Brandon", "Shirley", "Benjamin", "Angela", "Samuel", "Brenda", "Raymond", "Lisa",
    "Patrick", "Beverly", "Alexander", "Diane", "Jack", "Julie", "Dennis", "Joyce",
    "Jerry", "Victoria", "Tyler", "Olivia", "Aaron", "Kelly", "Jose", "Christina",
    "Adam", "Lauren", "Henry", "Joan", "Douglas", "Evelyn", "Zachary", "Judith",
    "Peter", "Megan", "Kyle", "Cheryl", "Walter", "Andrea", "Harold", "Hannah",
    "Jeremy", "Jacqueline", "Keith", "Martha", "Roger", "Madison", "Arthur", "Teresa",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Young",
    "Flores", "Green", "Nelson", "Carter", "Mitchell", "Roberts", "Phillips", "Campbell",
    "Parker", "Evans", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales",
    "Murphy", "Cook", "Rogers", "Morgan", "Peterson", "Cooper", "Reed", "Bell",
    "Gomez", "Russell", "Hayes", "Myers", "Ford", "Hamilton", "Graham", "Sullivan",
    "Wallace", "Woods", "Cole", "West", "Jordan", "Owens", "Reynolds", "Fisher",
    "Ellis", "Harper", "Mason", "Howell", "Kinney", "Shields", "Sharpe", "Bond",
    "Riley", "Carpenter", "Keller", "Bradford", "Knight", "Goodwin", "Marsh", "Proctor",
    "Woodard", "Schwartz", "Benson", "Deleon", "Franks", "Graves", "Hilton", "Holbrook",
]

# Special roles mapping (role names must match RBAC service)
SPECIAL_ROLES = {
    "supervisor": "supervisor",
    "manager": "manager",
    "human_resource": "human_resource",
    "finance": "finance",
    "it": "it",
    "agent": "agent",  # Default/Operations role
}

def generate_email(first_name: str, last_name: str, employee_no: str) -> str:
    """Generate a unique email address using employee number"""
    return f"{first_name.lower()}.{last_name.lower()}.{employee_no.lower()}@bpo-operations.com"

def generate_phone() -> str:
    """Generate a random phone number"""
    return f"+63{random.randint(9, 9)}{random.randint(0, 9)}{random.randint(10000000, 99999999)}"

def generate_date_of_joining() -> date:
    """Generate a random date of joining in the past 3 years"""
    days_back = random.randint(30, 365 * 3)
    return date.today() - timedelta(days=days_back)

def get_role_by_name(role_name: str, db: Session) -> Role:
    """Get a role from the database by name"""
    role = db.query(Role).filter(Role.name == role_name).first()
    return role

def calculate_remaining_campaigns_needed(employees_created: int, campaigns_created: int) -> int:
    """
    Calculate how many campaigns are still needed for remaining employees.
    Strategy: Assign 2-3 employees per campaign
    """
    remaining = TOTAL_EMPLOYEES - employees_created
    
    # If 0 or 1 employees left, return current campaign count
    if remaining <= 1:
        return campaigns_created
    
    # If 2-3 left, need 1 more campaign
    if remaining <= 3:
        return campaigns_created + 1
    
    # Otherwise, calculate based on 2.5 avg per campaign
    return campaigns_created + max(1, (remaining + 1) // 3)

def seed_employees(db: Session):
    """
    Seed the database with exactly 250 employees across 80+ campaigns (2-3 per campaign).
    
    Distribution:
    - 10 Supervisors
    - 1 Project Manager
    - 3 Human Resources
    - 1 Payroll / Finance
    - 2 IT
    - 233 Operations (agent role)
    """
    print("Starting employee seed process...")
    # Check if employees already exist (exclude admin user E001)
    existing_count = db.query(User).filter(User.employee_no != "E001").count()
    if existing_count >= 35:
        print(f"Database already has {existing_count} employees. Skipping seed...")
        return

    # Hardcoded campaign and status distribution
    seed_data = [
        # Campaign 1: 1 Active, 2 Inactive
        ("Campaign 1", "Active"), ("Campaign 1", "Inactive"), ("Campaign 1", "Inactive"),
        # Campaign 2: 2 Active
        ("Campaign 2", "Active"), ("Campaign 2", "Active"),
        # Campaign 3: 2 Active
        ("Campaign 3", "Active"), ("Campaign 3", "Active"),
        # Campaign 4: 2 Active
        ("Campaign 4", "Active"), ("Campaign 4", "Active"),
        # Campaign 5: 2 Active
        ("Campaign 5", "Active"), ("Campaign 5", "Active"),
        # Campaign 6: 4 Active
        ("Campaign 6", "Active"), ("Campaign 6", "Active"), ("Campaign 6", "Active"), ("Campaign 6", "Active"),
        # Campaign 7: 6 Active
        ("Campaign 7", "Active"), ("Campaign 7", "Active"), ("Campaign 7", "Active"), ("Campaign 7", "Active"), ("Campaign 7", "Active"), ("Campaign 7", "Active"),
        # Campaign 8: 2 Active
        ("Campaign 8", "Active"), ("Campaign 8", "Active"),
        # Campaign 9: 8 Inactive, 1 Transfer
        ("Campaign 9", "Inactive"), ("Campaign 9", "Inactive"), ("Campaign 9", "Inactive"), ("Campaign 9", "Inactive"), ("Campaign 9", "Inactive"), ("Campaign 9", "Inactive"), ("Campaign 9", "Inactive"), ("Campaign 9", "Inactive"), ("Campaign 9", "Transfer"),
        # Campaign 10: 1 Active
        ("Campaign 10", "Active"),
        # Campaign 11: 1 Active, 1 Inactive
        ("Campaign 11", "Active"), ("Campaign 11", "Inactive"),
    ]

    # Use a fixed set of names for uniqueness
    names = [(f"Test{i+1}", f"User{i+1}") for i in range(35)]
    departments = DEPARTMENTS * ((35 // len(DEPARTMENTS)) + 1)
    today = date.today()
    employee_num = 1001
    for idx, ((campaign, status), (first_name, last_name), department) in enumerate(zip(seed_data, names, departments)):
        employee_no = f"E{employee_num:05d}"
        email = generate_email(first_name, last_name, employee_no)
        role = get_role_by_name("agent", db)
        date_of_joining = today - timedelta(days=30 + idx)
        tenure_months = (today.year - date_of_joining.year) * 12 + (today.month - date_of_joining.month)
        try:
            employee = User(
                employee_no=employee_no,
                email=email,
                hashed_password=get_password_hash(f"password{employee_num}"),
                full_name=f"{first_name} {last_name}",
                role_id=role.id if role else None,
                campaign=campaign,
                department=department,
                phone_no=generate_phone(),
                personal_email=f"personal.{employee_no}@gmail.com",
                client_email=f"{employee_no}@client.bpo.com",
                date_of_joining=date_of_joining,
                tenure_months=tenure_months,
                employee_status=status,
                is_active=(status == "Active"),
                assessment_due_date=today + timedelta(days=60 + idx),
                regularization_date=date_of_joining + timedelta(days=180)
            )
            db.add(employee)
            employee_num += 1
        except Exception as e:
            print(f"  Error creating employee {employee_no}: {str(e)}")
            db.rollback()
            continue
    db.commit()
    print(f"\nSuccessfully seeded 35 employees across 11 campaigns!")
    print(f"Total employees in database: {db.query(User).count()}")
    # Print campaign breakdown
    print("\nCampaign Distribution:")
    campaigns = db.query(User.campaign, func.count(User.id)).filter(
        User.campaign.isnot(None),
        User.employee_no != "E001"  # Exclude admin
    ).group_by(User.campaign).order_by(User.campaign).all()
    for campaign_name, count in campaigns:
        print(f"  {campaign_name}: {count} employees")
    print(f"\n  Total campaigns: {len(campaigns)}")
    # Print status breakdown
    print("\nStatus Distribution:")
    status_data = db.query(User.employee_status, func.count(User.id)).filter(
        User.employee_no != "E001"  # Exclude admin
    ).group_by(User.employee_status).order_by(User.employee_status).all()
    for status, count in status_data:
        print(f"  {status}: {count} employees")

if __name__ == "__main__":
    from sqlalchemy import func
    db = SessionLocal()
    try:
        seed_employees(db)
    finally:
        db.close()
