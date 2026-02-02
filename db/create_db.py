import os

from sqlalchemy import create_engine
from db.models import metadata
from dotenv import load_dotenv

import sys
from loguru import logger
logger.remove()
logger.add(sys.stderr, level="INFO")

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost/{DB_NAME}")

def create_db():
    metadata.create_all(engine)
    logger.info('База данных и таблицы созданы.')

if __name__ == '__main__':
    create_db()