from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

from sqlmodel import Session

load_dotenv()

DATABASE_URL = (f"postgresql://postgres:{os.getenv('DB_PASSWORD')}@localhost:5432/Working_report_table")
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session