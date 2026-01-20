from fastapi import FastAPI
from app.users_router import router as users_router
from app.jobs_router import router as jobs_router

app = FastAPI()
app.include_router(jobs_router)
app.include_router(users_router)

# uvicorn app.main:app --reload