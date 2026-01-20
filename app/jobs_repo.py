'''
app.jobs_repo의 Docstring
jobs 레포지토리 계층은 DB만 다룹니다.
특징으로 HTTP를 모르며 status 의미도 모릅니다. 가져와라/저장해라만 합니다.
'''

from sqlmodel import Session, select
from app.models import Job


def get_job_by_id(session: Session, job_id: int) -> Job | None:
    return session.get(Job, job_id)


def save_job(session: Session, job: Job) -> Job:
    session.add(job)
    session.commit()
    session.refresh(job)
    return job
