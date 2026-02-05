# app/attachments_router.py
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from sqlmodel import Session, func, select
from app.db import get_session
from app.models import Attachment
from app.s3 import build_file_key, create_presigned_get_url, create_presigned_put_url
from app.works_repo import get_work_log_by_id
from app.works_service import ensure_today_work_log  # 네 repo 함수명에 맞게 바꿔도 됨

router = APIRouter(prefix="/attachments", tags=["attachments"])

class PresignRequest(BaseModel):
    work_log_id: int
    filename: str
    content_type: str  # "image/jpeg" 같은 값

class PresignResponse(BaseModel):
    upload_url: str
    file_key: str

class PresignGetRequest(BaseModel):
    file_key: str
    expires_in: int = 600
    response_content_type: str | None = None  # 예: "image/png"
    as_attachment: bool = False
    download_filename: str | None = None

@router.post("/presign", response_model=PresignResponse)
def presign_upload(req: PresignRequest, session: Session = Depends(get_session)):
    # 1) work_log 존재 확인
    work_log = get_work_log_by_id(session, req.work_log_id)
    if not work_log:
        raise HTTPException(status_code=404, detail="work_log not found")

    # 2) (선택) 휴무면 업로드 불가 — 너 도메인에 맞게 status/worked 체크
    # 예: work_log.status == WorkStatus.OFF
    # if work_log.status == WorkStatus.OFF:
    #     raise HTTPException(status_code=400, detail="off day cannot upload")

    # 3) file_key 생성
    file_key = build_file_key(work_log.work_date, req.filename)

    # 4) presigned url 생성
    upload_url = create_presigned_put_url(
        file_key=file_key,
        content_type=req.content_type,
        expires_in=60,  # 60초면 충분
    )

    return PresignResponse(upload_url=upload_url, file_key=file_key)

@router.post("/presign-get")
def presign_get(payload: PresignGetRequest):
    if not payload.file_key:
        raise HTTPException(status_code=400, detail="file_key is required")

    url = create_presigned_get_url(
        file_key=payload.file_key,
        expires_in=payload.expires_in,
        response_content_type=payload.response_content_type,
        as_attachment=payload.as_attachment,
        download_filename=payload.download_filename,
    )
    return {"download_url": url, "file_key": payload.file_key}

class ConfirmRequest(BaseModel):
    work_log_id: int
    file_key: str
    original_filename: str

class ConfirmResponse(BaseModel):
    id: int
    work_log_id: int
    file_key: str
    original_filename: str
    created_at: str #원하면 datetime도 오케이

def _is_off_day(work_log) -> bool:
    """
    work_log.status가 Enum일 수도, str일 수도 있어서 안전하게 처리.
    """
    status = getattr(work_log, "status", None)
    if status is None:
        return False

    # Enum이면 .value, 아니면 그대로 비교
    value = getattr(status, "value", status)
    return value == "휴무"

@router.post("/confirm", response_model=ConfirmResponse)
def confirm_attachment(req: ConfirmRequest, session: Session = Depends(get_session)):
    # 1) work_log 존재 확인
    work_log = get_work_log_by_id(session, req.work_log_id)
    if not work_log:
        raise HTTPException(status_code=404, detail="work_log not found")

    # 2) 휴무일이면 불가
    # status_value = getattr(getattr(work_log.status, "value", work_log.status), "strip", lambda: work_log.status)()
    # if status_value == "휴무":
    #     raise HTTPException(status_code=400, detail="off day cannot attach files")

    # 3) 멱등성: 이미 있으면 그대로 반환
    stmt = select(Attachment).where(
        Attachment.work_log_id == req.work_log_id,
        Attachment.file_key == req.file_key,
    )
    existing = session.exec(stmt).first()
    if existing:
        return ConfirmResponse(
            id=existing.id,
            work_log_id=existing.work_log_id,
            file_key=existing.file_key,
            original_filename=existing.original_filename,
            created_at=existing.created_at.isoformat() if existing.created_at else "",
        )

    # 3.5) 하루 최대 3장 제한
    count_stmt = select(func.count()).select_from(Attachment).where(
        Attachment.work_log_id == req.work_log_id
    )
    current_count = session.exec(count_stmt).one()

    if int(current_count) >= 3:
        raise HTTPException(status_code=400, detail="오늘은 사진을 최대 3장까지 올릴 수 있어요.")

    # 4) 없으면 생성
    attachment = Attachment(
        work_log_id=req.work_log_id,
        file_key=req.file_key,
        original_filename=req.original_filename,
    )

    session.add(attachment)
    session.commit()
    session.refresh(attachment)

    return ConfirmResponse(
        id=attachment.id,
        work_log_id=attachment.work_log_id,
        file_key=attachment.file_key,
        original_filename=attachment.original_filename,
        created_at=attachment.created_at.isoformat() if attachment.created_at else "",
    )

class PresignTodayRequest(BaseModel):
    filename: str
    content_type: str

class PresignTodayResponse(BaseModel):
    upload_url: str
    file_key: str
    work_log_id: int

@router.post("/presign/today", response_model=PresignTodayResponse)
def presign_today(req: PresignTodayRequest, session: Session = Depends(get_session)):
    wl = ensure_today_work_log(session)

    status_value = getattr(wl.status, "value", wl.status)
    if status_value == "휴무":
        raise HTTPException(status_code=400, detail="휴무 상태에서는 사진 업로드가 불가합니다. 출근으로 변경 후 업로드하세요.")

    file_key = build_file_key(wl.work_date, req.filename)

    upload_url = create_presigned_put_url(
        file_key=file_key,
        content_type=req.content_type,
        expires_in=600,  # 너가 10분으로 늘린 흐름과 통일
    )

    return PresignTodayResponse(upload_url=upload_url, file_key=file_key, work_log_id=wl.id)