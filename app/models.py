from typing import Optional
from datetime import datetime, date
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, nullable=False)
    created_at: Optional[datetime] = Field(default=None)

class Job(SQLModel, table=True):
    __tablename__ = "jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    work_date: date = Field(nullable=False)
    company_name: str = Field(max_length=255, nullable=False)
    site_name: str = Field(max_length=255, nullable=False)
    amount: int = Field(nullable=False)
    status: str = Field(default="UNPAID", max_length=10, nullable=False)
    memo: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)