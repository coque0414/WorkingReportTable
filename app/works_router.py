'''
app.jobs_router의 Docstring (리팩토링 버전)
work_logs 관련 HTTP 엔드포인트 정의
Request -> Service 호출 -> Response 반환만 함
'''

from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from sqlalchemy import func
from sqlmodel import Session, select
from app.db import get_session
from app.models import Attachment, WorkLog, WorkStatus
from app.s3 import create_presigned_get_url
from app.works_service import (
    create_or_update_work_log,
    ensure_today_work_log,
    get_all_work_logs,
    get_work_logs_by_status,
    get_total_sales_amount,
    get_work_log,
)

router = APIRouter(prefix="/work-logs", tags=["work_logs"])


class WorkLogUpsertRequest(BaseModel):
    work_date: date
    status: WorkStatus
    sales_count: int = 0
    sales_amount: int = 0
    note: str | None = None


@router.get("/")
def read_work_logs(session: Session = Depends(get_session)):
    return get_all_work_logs(session)

@router.get("/today")
def get_today(session: Session = Depends(get_session)):
    wl = ensure_today_work_log(session)

    att_stmt = (
        select(Attachment)
        .where(Attachment.work_log_id == wl.id)
        .order_by(Attachment.created_at.asc())
    )
    atts = session.exec(att_stmt).all()

    return {
        "id": wl.id,
        "work_date": str(wl.work_date),
        "status": getattr(wl.status, "value", wl.status),
        "sales_count": wl.sales_count,
        "sales_amount": wl.sales_amount,
        "note": wl.note,
        "created_at": wl.created_at.isoformat() if wl.created_at else "",
        "updated_at": wl.updated_at.isoformat() if wl.updated_at else "",
        "attachments": [
            {
                "id": a.id,
                "file_key": a.file_key,
                "original_filename": a.original_filename,
                "created_at": a.created_at.isoformat() if a.created_at else "",
            }
            for a in atts
        ],
    }

class TodaySalesPatchRequest(BaseModel):
    sales_count: int | None = None
    sales_amount: int | None = None

@router.patch("/today/sales")
def patch_today_sales(payload: TodaySalesPatchRequest, session: Session = Depends(get_session)):
    wl = ensure_today_work_log(session)

    status_value = getattr(wl.status, "value", wl.status)
    if status_value == "휴무":
        raise HTTPException(status_code=400, detail="휴무 상태에서는 판매 입력이 불가합니다. 출근으로 변경 후 입력하세요.")

    if payload.sales_count is None and payload.sales_amount is None:
        raise HTTPException(status_code=400, detail="sales_count 또는 sales_amount 중 하나는 필요합니다.")

    if payload.sales_count is not None and payload.sales_count < 0:
        raise HTTPException(status_code=400, detail="sales_count는 음수일 수 없습니다.")
    if payload.sales_amount is not None and payload.sales_amount < 0:
        raise HTTPException(status_code=400, detail="sales_amount는 음수일 수 없습니다.")

    if payload.sales_count is not None:
        wl.sales_count = payload.sales_count
    if payload.sales_amount is not None:
        wl.sales_amount = payload.sales_amount

    # updated_at은 server_default만 있으면 자동 갱신 안 될 수 있어서
    # DB 트리거/DEFAULT 설정이 없다면 서비스에서 직접 찍어도 됨(선택)
    # wl.updated_at = datetime.utcnow()

    session.add(wl)
    session.commit()
    session.refresh(wl)

    return {
        "id": wl.id,
        "work_date": str(wl.work_date),
        "status": getattr(wl.status, "value", wl.status),
        "sales_count": wl.sales_count,
        "sales_amount": wl.sales_amount,
        "note": wl.note,
    }

@router.get("/today/detail")
def get_today_detail(session: Session = Depends(get_session)):
    wl = ensure_today_work_log(session)

    att_stmt = (
        select(Attachment)
        .where(Attachment.work_log_id == wl.id)
        .order_by(Attachment.created_at.asc())
    )
    atts = session.exec(att_stmt).all()

    return {
        "date": str(wl.work_date),
        "work_log": {
            "id": wl.id,
            "status": getattr(wl.status, "value", wl.status),
            "sales_count": wl.sales_count,
            "sales_amount": wl.sales_amount,
            "note": wl.note,
        },
        "attachments": [
            {
                "id": a.id,
                "file_key": a.file_key,
                "original_filename": a.original_filename,
                "view_url": create_presigned_get_url(
                    file_key=a.file_key,
                    expires_in=600,
                    response_content_type=None,
                    as_attachment=False,
                ),
            }
            for a in atts
        ],
    }

@router.get("/status/{status}")
def read_work_logs_by_status(status: WorkStatus, session: Session = Depends(get_session)):
    return get_work_logs_by_status(session, status)


@router.post("/upsert")
def upsert_work_log(payload: WorkLogUpsertRequest, session: Session = Depends(get_session)):
    try:
        return create_or_update_work_log(
            session=session,
            work_date=payload.work_date,
            status=payload.status,
            sales_count=payload.sales_count,
            sales_amount=payload.sales_amount,
            note=payload.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/summary/total-sales-amount")
def read_total_sales_amount(session: Session = Depends(get_session)):
    total = get_total_sales_amount(session)
    return {"total_sales_amount": total}

class AttachmentItem(BaseModel):
    id: int
    file_key: str
    original_filename: str
    created_at: str

class WorkLogWithAttachmentsResponse(BaseModel):
    id: int
    work_date: str
    status: str
    sales_count: int
    sales_amount: int
    note: str | None
    created_at: str
    updated_at: str
    attachments: list[AttachmentItem]

#오늘기준으로 worklog찾아서 attachment에서 다운로드url까지
class TodayPhotoItem(BaseModel):
    attachment_id: int
    original_filename: str
    file_key: str
    download_url: str

@router.get("/today/photos", response_model=list[TodayPhotoItem])
def get_today_photos(session: Session = Depends(get_session)):
    today = date.today()

    log_stmt = select(WorkLog).where(WorkLog.work_date == today)
    log = session.exec(log_stmt).first()
    if not log:
        return []

    # 휴무면 사진 보기 자체를 막고 싶으면 여기서도 체크 가능(선택)
    status_value = getattr(getattr(log.status, "value", log.status), "strip", lambda: log.status)()
    if status_value == "휴무":
        return []

    att_stmt = select(Attachment).where(Attachment.work_log_id == log.id)
    atts = session.exec(att_stmt).all()

    items: list[TodayPhotoItem] = []
    for a in atts:
        url = create_presigned_get_url(
            file_key=a.file_key,
            expires_in=600,  # 10분
            response_content_type=None,  # 굳이 강제하지 않아도 됨
            as_attachment=False,
        )
        items.append(
            TodayPhotoItem(
                attachment_id=a.id,
                original_filename=a.original_filename,
                file_key=a.file_key,
                download_url=url,
            )
        )

    return items

@router.get("/week-summary")
def week_summary(session: Session = Depends(get_session)):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # 월요일
    week_end = week_start + timedelta(days=6)

    # 출근일 수
    work_days_stmt = select(func.count()).select_from(WorkLog).where(
        WorkLog.work_date >= week_start,
        WorkLog.work_date <= week_end,
        WorkLog.status == WorkStatus.출근,
    )
    work_days = session.exec(work_days_stmt).one()

    # 판매 합계
    sales_sum_stmt = select(func.coalesce(func.sum(WorkLog.sales_amount), 0)).where(
        WorkLog.work_date >= week_start,
        WorkLog.work_date <= week_end,
    )
    sales_amount_sum = session.exec(sales_sum_stmt).one()

    # 사진 업로드한 날 수 (attachments 있는 날짜 distinct)
    photo_days_stmt = select(func.count(func.distinct(WorkLog.work_date))).select_from(WorkLog).join(
        Attachment, Attachment.work_log_id == WorkLog.id
    ).where(
        WorkLog.work_date >= week_start,
        WorkLog.work_date <= week_end,
    )
    photo_days = session.exec(photo_days_stmt).one()

    return {
        "week_start": str(week_start),
        "week_end": str(week_end),
        "work_days": int(work_days),
        "sales_amount_sum": int(sales_amount_sum),
        "photo_days": int(photo_days),
    }

@router.get("/{id}")
def read_work_log(id: int, session: Session = Depends(get_session)):
    log = get_work_log(session, id)
    if not log:
        raise HTTPException(status_code=404, detail="WorkLog not found")
    return log

@router.get("/{id}/detail", response_model=WorkLogWithAttachmentsResponse)
def read_work_log_detail(id: int, session: Session = Depends(get_session)):
    log = get_work_log(session, id)   # 너 기존 service 사용
    if not log:
        raise HTTPException(status_code=404, detail="WorkLog not found")

    att_stmt = (
        select(Attachment)
        .where(Attachment.work_log_id == id)
        .order_by(Attachment.created_at.asc())
    )
    atts = session.exec(att_stmt).all()

    def sv(x):
        return getattr(getattr(x, "value", x), "strip", lambda: x)()

    return WorkLogWithAttachmentsResponse(
        id=log.id,
        work_date=str(log.work_date),
        status=sv(log.status),
        sales_count=log.sales_count,
        sales_amount=log.sales_amount,
        note=log.note,
        created_at=log.created_at.isoformat() if log.created_at else "",
        updated_at=log.updated_at.isoformat() if log.updated_at else "",
        attachments=[
            AttachmentItem(
                id=a.id,
                file_key=a.file_key,
                original_filename=a.original_filename,
                created_at=a.created_at.isoformat() if a.created_at else "",
            )
            for a in atts
        ],
    )