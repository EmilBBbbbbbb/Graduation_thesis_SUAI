from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from sqlalchemy import select, desc

from db.core import engine
from db.models import (
    gold_cost_table,
    silver_cost_table,
    copper_cost_table,
    gold_news_table,
    silver_news_table,
    copper_news_table,
    gold_cost_predict_table,
    silver_cost_predict_table,
    copper_cost_predict_table,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def fetch_candles(table, start_date: datetime | None = None):
    if start_date is None:
        start_date = datetime(2019, 1, 1)

    with engine.connect() as connection:
        stmt = (
            select(table)
            .where(table.c.date >= start_date)
            .order_by(table.c.date)
        )
        rows = connection.execute(stmt).mappings().all()

    data = []
    for row in rows:
        date_value = row.get("date")
        data.append(
            {
                "time": date_value.strftime("%Y-%m-%d") if date_value else "",
                "open": round(row.get("open", 0.0), 2),
                "high": round(row.get("high", 0.0), 2),
                "low": round(row.get("low", 0.0), 2),
                "close": round(row.get("close", 0.0), 2),
            }
        )

    return data


def fetch_predict_candles(table, start_date: datetime | None = None):
    if start_date is None:
        start_date = datetime(2019, 1, 1)

    with engine.connect() as connection:
        stmt = (
            select(table)
            .where(table.c.date >= start_date)
            .order_by(table.c.date)
        )
        rows = connection.execute(stmt).mappings().all()

    data = []
    for row in rows:
        date_value = row.get("date")
        data.append(
            {
                "time": date_value.strftime("%Y-%m-%d") if date_value else "",
                "open": round(row.get("open", 0.0), 2),
                "high": round(row.get("high", 0.0), 2),
                "low": round(row.get("low", 0.0), 2),
                "close": round(row.get("close", 0.0), 2),
            }
        )

    return data


def fetch_news(table):
    with engine.connect() as connection:
        stmt = select(table).order_by(desc(table.c.date), desc(table.c.id))
        rows = connection.execute(stmt).mappings().all()

    news = []
    for row in rows:
        date_value = row.get("date")
        news.append(
            {
                "title": row.get("title") or "",
                "date": date_value.strftime("%d.%m.%Y") if date_value else "",
                "summary": row.get("description") or "",
                "body": row.get("full_text") or "",
            }
        )

    return news


def render_metal(request: Request, metal_key: str):
    metals = {
        "gold": {
            "name": "Золото",
            "code": "XAU",
            "cost_table": gold_cost_table,
            "predict_table": gold_cost_predict_table,
            "news_table": gold_news_table,
        },
        "silver": {
            "name": "Серебро",
            "code": "XAG",
            "cost_table": silver_cost_table,
            "predict_table": silver_cost_predict_table,
            "news_table": silver_news_table,
        },
        "cupp": {
            "name": "Медь",
            "code": "Cu",
            "cost_table": copper_cost_table,
            "predict_table": copper_cost_predict_table,
            "news_table": copper_news_table,
        },
    }
    metal = metals.get(metal_key, metals["gold"])
    chart_data = fetch_candles(metal["cost_table"])
    predict_data = fetch_predict_candles(metal["predict_table"])


    context = {
        "request": request,
        "year": datetime.now().year,
        "metal_name": metal["name"],
        "metal_code": metal["code"],
        "chart_data": chart_data,
        "predict_data": predict_data,
        "news": fetch_news(metal["news_table"]),
    }
    return templates.TemplateResponse("index.html", context)


@router.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return render_metal(request, "gold")


@router.get('/gold', response_class=HTMLResponse)
async def gold(request: Request):
    return render_metal(request, "gold")


@router.get('/silver', response_class=HTMLResponse)
async def silver(request: Request):
    return render_metal(request, "silver")


@router.get('/cupp', response_class=HTMLResponse)
async def cupp(request: Request):
    return render_metal(request, "cupp")
