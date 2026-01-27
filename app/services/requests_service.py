from sqlalchemy.orm import Session
from app.models.requests import Request
from app.schemas.requests import RequestCreate
from typing import List, Optional

def get_requests(db: Session, user_id: Optional[int] = None) -> List[Request]:
    query = db.query(Request)
    if user_id:
        query = query.filter(Request.user_id == user_id)
    return query.order_by(Request.created_at.desc()).all()

def get_request(db: Session, request_id: int) -> Optional[Request]:
    return db.query(Request).filter(Request.id == request_id).first()

def create_request(db: Session, user_id: int, request_in: RequestCreate) -> Request:
    db_request = Request(user_id=user_id, type=request_in.type, details=request_in.details)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

def update_request(db: Session, request_id: int, data: dict) -> Optional[Request]:
    db_request = get_request(db, request_id)
    if not db_request:
        return None
    for key, value in data.items():
        setattr(db_request, key, value)
    db.commit()
    db.refresh(db_request)
    return db_request

def delete_request(db: Session, request_id: int) -> bool:
    db_request = get_request(db, request_id)
    if not db_request:
        return False
    db.delete(db_request)
    db.commit()
    return True
