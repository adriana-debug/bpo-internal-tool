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
