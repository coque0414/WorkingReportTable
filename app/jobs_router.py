from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import get_session
from app.models import Job
from app.jobs_service import mark_job_paid

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("/")
def read_jobs(session: Session = Depends(get_session)):
    jobs = session.exec(select(Job)).all()
    return jobs

@router.get("/unpaid")
def read_unpaid_jobs(session: Session = Depends(get_session)):
    unpaid_jobs = session.exec(select(Job)
                            .where(Job.status == "UNPAID")
                            .order_by(Job.work_date.asc())
                            ).all()
    return unpaid_jobs

@router.patch("/{id}/mark_paid")
def mark_job_paid(id:int, session: Session = Depends(get_session)):
    job = session.get(Job, id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = "PAID"
    session.add(job)
    session.commit()
    session.refresh(job)
    return job

@router.get("/unpaid/summary")
def get_unpaid_jobs_summary(session: Session = Depends(get_session)):
    summary = session.exec(
        select(func.sum(Job.amount))
            .where(Job.status == "UNPAID")).first() or 0
    return {"total_amount": summary}