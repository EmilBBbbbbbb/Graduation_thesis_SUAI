import os

from sqlalchemy import create_engine
from db.models import metadata
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost/{DB_NAME}")

def create_db():
    metadata.create_all(engine)

if __name__ == '__main__':
    create_db()