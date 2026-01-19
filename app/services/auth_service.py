from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import verify_password, get_password_hash

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_user(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    employee_no: str,
    role_id: int = None,
    campaign: str = None,
    department: str = None
) -> User:
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        employee_no=employee_no,
        role_id=role_id,
        campaign=campaign,
        department=department
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
