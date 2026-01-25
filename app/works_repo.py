'''
app.jobs_repo의 Docstring (리팩토링 버전)
work_logs 레포지토리 계층은 DB만 다룹니다.
HTTP를 모르며, 비즈니스 규칙도 모릅니다. 가져와라/저장해라만 합니다.
'''

from datetime import date
from sqlalchemy import func
from sqlmodel import Session, select

from app.models import WorkLog, WorkStatus


def get_work_log_by_id(session: Session, log_id: int) -> WorkLog | None:
    return session.get(WorkLog, log_id)


def get_work_log_by_date(session: Session, work_date: date) -> WorkLog | None:
    statement = select(WorkLog).where(WorkLog.work_date == work_date)
    return session.exec(statement).first()


def save_work_log(session: Session, log: WorkLog) -> WorkLog:
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def list_work_logs(session: Session) -> list[WorkLog]:
    statement = select(WorkLog).order_by(WorkLog.work_date.desc())
    return session.exec(statement).all()


def list_work_logs_by_status(session: Session, status: WorkStatus) -> list[WorkLog]:
    statement = (
        select(WorkLog)
        .where(WorkLog.status == status)
        .order_by(WorkLog.work_date.asc())
    )
    return session.exec(statement).all()


def sum_sales_amount(session: Session) -> int:
    statement = select(func.coalesce(func.sum(WorkLog.sales_amount), 0))
    result = session.exec(statement).scalar_one_or_none()
    return int(result or 0)
