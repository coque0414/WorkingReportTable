'''
app.jobs_service의 Docstring
이 파일에서는 어떻게 처리할지 결정합니다.
벌어지는 일의 예시로는 
PAID의 상태를 다시 바꾸지 않는다, 
없는 job은 에러, paid로 바꾸는 행위의 규칙 등이 있습니다.(비즈니스 로직이라 함)
'''
from fastapi import HTTPException
from sqlmodel import Session

from app.jobs_repo import get_job_by_id, save_job


def mark_job_paid(session: Session, job_id: int):
    job = get_job_by_id(session, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 비즈니스 규칙
    if job.status == "PAID":
        return job  # 멱등성

    job.status = "PAID"
    return save_job(session, job)
