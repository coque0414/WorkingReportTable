from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
def read_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users