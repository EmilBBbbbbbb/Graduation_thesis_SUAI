from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes.general import router as general_router


app = FastAPI(title="Restaurant Website")

app.include_router(general_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Для запуска: uvicorn app.main:app --reload