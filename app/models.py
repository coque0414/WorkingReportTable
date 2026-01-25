from typing import Optional
from datetime import datetime, date
from enum import Enum

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, text
from sqlalchemy.dialects.postgresql import ENUM as PGEnum


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, nullable=False)
    created_at: Optional[datetime] = Field(default=None)


class WorkStatus(str, Enum):
    출근 = "출근"
    휴무 = "휴무"
    반차 = "반차"


class WorkLog(SQLModel, table=True):
    __tablename__ = "work_logs"

    id: Optional[int] = Field(default=None, primary_key=True)

    work_date: date = Field(nullable=False, index=True)

    sales_count: int = Field(default=0, nullable=False)
    sales_amount: int = Field(default=0, nullable=False)

    status: WorkStatus = Field(
        sa_column=Column(
            PGEnum(WorkStatus, name="work_status", create_type=False),
            nullable=False,
        )
    )

    note: Optional[str] = Field(default=None)

# orm의 null을 보냄 이슈로 db default가 안먹혀서 orm은 insert 관여안하게 셀렉시 그냥 읽는것으로
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=False, server_default=text("now()")),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=False, server_default=text("now()")),
    )

class Attachment(SQLModel, table=True):
    __tablename__ = "attachments"

    id: Optional[int] = Field(default=None, primary_key=True)

    work_log_id: int = Field(foreign_key="work_logs.id", nullable=False, index=True)

    file_key: str = Field(nullable=False, max_length=1024)
    original_filename: str = Field(nullable=False, max_length=255)

    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=False, server_default=text("now()")),
    )