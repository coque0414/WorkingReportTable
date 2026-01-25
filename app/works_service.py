'''
app.jobs_service의 Docstring (리팩토링 버전)
work_logs에서 어떻게 처리할지 결정합니다 (비즈니스 로직).
예: 휴무일엔 매출 0 강제, work_date 유니크 기반 upsert 등
'''

from datetime import date
from sqlmodel import Session

from app.models import WorkLog, WorkStatus
from app.works_repo import (
    get_work_log_by_id,
    get_work_log_by_date,
    list_work_logs,
    list_work_logs_by_status,
    save_work_log,
    sum_sales_amount,
)


def _validate_non_negative(value: int, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name}는 0 이상이어야 합니다.")


def create_or_update_work_log(
    session: Session,
    work_date: date,
    status: WorkStatus,
    sales_count: int = 0,
    sales_amount: int = 0,
    note: str | None = None,
) -> WorkLog:
    _validate_non_negative(sales_count, "sales_count")
    _validate_non_negative(sales_amount, "sales_amount")

    # 비즈니스 규칙: 휴무면 매출/판매수는 0으로 강제
    if status == WorkStatus.휴무:
        sales_count = 0
        sales_amount = 0

    existing = get_work_log_by_date(session, work_date)
    if existing:
        existing.status = status
        existing.sales_count = sales_count
        existing.sales_amount = sales_amount
        existing.note = note
        return save_work_log(session, existing)

    new_log = WorkLog(
        work_date=work_date,
        status=status,
        sales_count=sales_count,
        sales_amount=sales_amount,
        note=note,
    )

    # DB default 쓰려면 ORM이 NULL을 보내면 안 됨
    delattr(new_log, "created_at")
    delattr(new_log, "updated_at")
    
    return save_work_log(session, new_log)


def get_all_work_logs(session: Session) -> list[WorkLog]:
    return list_work_logs(session)


def get_work_logs_by_status(session: Session, status: WorkStatus) -> list[WorkLog]:
    return list_work_logs_by_status(session, status)


def get_total_sales_amount(session: Session) -> int:
    return sum_sales_amount(session)


def get_work_log(session: Session, log_id: int) -> WorkLog | None:
    return get_work_log_by_id(session, log_id)
