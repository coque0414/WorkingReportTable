from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.users_router import router as users_router
from app.works_router import router as jobs_router
from app.attachments_router import router as attachments_router

app = FastAPI()
app.include_router(jobs_router)
app.include_router(users_router)
app.include_router(attachments_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# python -m uvicorn app.main:app --reload
