import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.routes.general import router as general_router


app = FastAPI(title="Restaurant Website")

app.add_middleware(
	SessionMiddleware,
	secret_key=os.getenv("SESSION_SECRET_KEY", "dev-session-secret-key-change-me"),
	same_site="lax",
)

app.include_router(general_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Для запуска: uvicorn app.main:app --reload