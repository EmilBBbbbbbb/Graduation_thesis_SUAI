import hashlib
import hmac
import os
import re
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, desc, insert, select, update

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
    users_table,
    demo_trades_table,
)


def calculate_rsi(prices, period=14):
    """Вычисление RSI (Relative Strength Index)"""
    if len(prices) < period + 1:
        return []
    
    rsi_values = []
    
    for i in range(period, len(prices)):
        gains = 0
        losses = 0
        
        for j in range(i - period, i):
            change = prices[j + 1] - prices[j]
            if change > 0:
                gains += change
            else:
                losses += abs(change)
        
        avg_gain = gains / period
        avg_loss = losses / period
        
        if avg_loss == 0:
            rsi = 100 if avg_gain > 0 else 0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append(rsi)
    
    return rsi_values


SQLI_PATTERN = re.compile(r"(--|;|/\*|\*/|\b(select|insert|update|delete|drop|union|alter|truncate)\b)", re.IGNORECASE)
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _contains_sqli_payload(value: str) -> bool:
    return bool(SQLI_PATTERN.search(value or ""))


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 120000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, iterations_raw, salt_hex, digest_hex = stored_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations_raw),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _set_flash(request: Request, message: str, level: str = "info") -> None:
    request.session["flash"] = {"message": message, "level": level}


def _pop_flash(request: Request) -> dict:
    return request.session.pop("flash", {"message": "", "level": ""})


def _get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    with engine.connect() as connection:
        stmt = select(users_table).where(users_table.c.id == int(user_id)).limit(1)
        return connection.execute(stmt).mappings().first()


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
    close_prices = []
    
    for row in rows:
        date_value = row.get("date")
        close_price = row.get("close", 0.0)
        close_prices.append(close_price)
        
        data.append(
            {
                "time": date_value.strftime("%Y-%m-%d") if date_value else "",
                "open": round(row.get("open", 0.0), 2),
                "high": round(row.get("high", 0.0), 2),
                "low": round(row.get("low", 0.0), 2),
                "close": round(close_price, 2),
                "volume": row.get("volume", 0),
            }
        )
    
    # Вычисление RSI
    rsi_values = calculate_rsi(close_prices)
    
    # Добавление RSI в данные (начиная с периода 14)
    for i, rsi_value in enumerate(rsi_values):
        if (i + 14) < len(data):
            data[i + 14]["rsi"] = round(rsi_value, 2)
    
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


def fetch_latest_close_price(table) -> float:
    with engine.connect() as connection:
        stmt = select(table.c.close).order_by(desc(table.c.date)).limit(1)
        row = connection.execute(stmt).first()
    if not row:
        return 0.0
    return round(float(row[0] or 0.0), 2)


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


def fetch_trade_history(user_id: int, limit: int = 50):
    with engine.connect() as connection:
        stmt = (
            select(demo_trades_table)
            .where(demo_trades_table.c.user_id == user_id)
            .order_by(desc(demo_trades_table.c.created_at), desc(demo_trades_table.c.id))
            .limit(limit)
        )
        rows = connection.execute(stmt).mappings().all()

    items = []
    for row in rows:
        items.append(
            {
                "metal_key": row.get("metal_key", ""),
                "side": row.get("side", ""),
                "quantity": round(float(row.get("quantity") or 0.0), 4),
                "price": round(float(row.get("price") or 0.0), 2),
                "total": round(float(row.get("total") or 0.0), 2),
                "created_at": row.get("created_at").strftime("%d.%m.%Y %H:%M") if row.get("created_at") else "",
            }
        )
    return items


def fetch_positions(user_id: int):
    with engine.connect() as connection:
        stmt = (
            select(demo_trades_table.c.metal_key, demo_trades_table.c.side, demo_trades_table.c.quantity)
            .where(demo_trades_table.c.user_id == user_id)
        )
        rows = connection.execute(stmt).mappings().all()

    positions = {}
    for row in rows:
        key = row.get("metal_key", "")
        quantity = float(row.get("quantity") or 0.0)
        if row.get("side") == "buy":
            positions[key] = positions.get(key, 0.0) + quantity
        elif row.get("side") == "sell":
            positions[key] = positions.get(key, 0.0) - quantity

    return {k: round(v, 4) for k, v in positions.items() if v > 0}


def compute_total_capital(user_id: int, cash_capital: float) -> float:
    prices_by_metal = {
        "gold": fetch_latest_close_price(gold_cost_table),
        "silver": fetch_latest_close_price(silver_cost_table),
        "cupp": fetch_latest_close_price(copper_cost_table),
    }
    positions = fetch_positions(user_id)

    positions_value = 0.0
    for metal_key, quantity in positions.items():
        positions_value += float(quantity) * float(prices_by_metal.get(metal_key, 0.0))

    return round(float(cash_capital) + positions_value, 2)


def compute_performance(start_capital: float, current_capital: float) -> float:
    if start_capital <= 0:
        return 0.0
    return round(((current_capital - start_capital) / start_capital) * 100, 2)


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
    current_user = _get_current_user(request)

    trade_history = []
    positions = {}
    display_current_capital = 0.0
    performance_pct = 0.0
    if current_user:
        user_id = int(current_user["id"])
        trade_history = fetch_trade_history(int(current_user["id"]))
        positions = fetch_positions(int(current_user["id"]))
        display_current_capital = compute_total_capital(
            user_id,
            float(current_user.get("current_capital") or 0.0),
        )
        performance_pct = compute_performance(
            float(current_user.get("start_capital") or 0.0),
            display_current_capital,
        )

    flash = _pop_flash(request)

    context = {
        "request": request,
        "year": datetime.now().year,
        "metal_name": metal["name"],
        "metal_code": metal["code"],
        "chart_data": chart_data,
        "predict_data": predict_data,
        "news": fetch_news(metal["news_table"]),
        "metal_key": metal_key,
        "latest_price": fetch_latest_close_price(metal["cost_table"]),
        "current_user": current_user,
        "trade_history": trade_history,
        "positions": positions,
        "display_current_capital": display_current_capital,
        "performance_pct": performance_pct,
        "flash_message": flash.get("message", ""),
        "flash_level": flash.get("level", ""),
    }
    return templates.TemplateResponse("index.html", context)


@router.post("/auth/register")
async def register(request: Request):
    form = await request.form()
    username = (form.get("username") or "").strip()
    email = (form.get("email") or "").strip().lower()
    password = (form.get("password") or "").strip()
    start_capital_raw = (form.get("start_capital") or "100000").strip()

    if not USERNAME_PATTERN.fullmatch(username) or _contains_sqli_payload(username):
        _set_flash(request, "Некорректный логин.", "error")
        return RedirectResponse("/", status_code=303)

    if not EMAIL_PATTERN.fullmatch(email) or _contains_sqli_payload(email):
        _set_flash(request, "Некорректный email.", "error")
        return RedirectResponse("/", status_code=303)

    if len(password) < 8:
        _set_flash(request, "Пароль должен быть не короче 8 символов.", "error")
        return RedirectResponse("/", status_code=303)

    try:
        start_capital = float(start_capital_raw)
    except ValueError:
        _set_flash(request, "Начальный капитал должен быть числом.", "error")
        return RedirectResponse("/", status_code=303)

    if start_capital <= 0:
        _set_flash(request, "Начальный капитал должен быть больше 0.", "error")
        return RedirectResponse("/", status_code=303)

    now = datetime.now()
    password_hash = _hash_password(password)

    with engine.begin() as connection:
        existing_stmt = select(users_table.c.id).where(
            (users_table.c.username == username) | (users_table.c.email == email)
        )
        existing_user = connection.execute(existing_stmt).first()
        if existing_user:
            _set_flash(request, "Пользователь с таким логином или email уже существует.", "error")
            return RedirectResponse("/", status_code=303)

        insert_stmt = insert(users_table).values(
            username=username,
            email=email,
            password_hash=password_hash,
            start_capital=start_capital,
            current_capital=start_capital,
            created_at=now,
        ).returning(users_table.c.id)
        new_user_id = connection.execute(insert_stmt).scalar_one()

    request.session["user_id"] = int(new_user_id)
    _set_flash(request, "Регистрация прошла успешно.", "success")
    return RedirectResponse("/", status_code=303)


@router.post("/auth/login")
async def login(request: Request):
    form = await request.form()
    username = (form.get("username") or "").strip()
    password = (form.get("password") or "").strip()

    if _contains_sqli_payload(username):
        _set_flash(request, "Неверные данные для входа.", "error")
        return RedirectResponse("/", status_code=303)

    with engine.connect() as connection:
        stmt = select(users_table).where(users_table.c.username == username).limit(1)
        user = connection.execute(stmt).mappings().first()

    if not user or not _verify_password(password, user.get("password_hash", "")):
        _set_flash(request, "Неверные данные для входа.", "error")
        return RedirectResponse("/", status_code=303)

    request.session["user_id"] = int(user["id"])
    _set_flash(request, "Вы вошли в систему.", "success")
    return RedirectResponse("/", status_code=303)


@router.post("/auth/logout")
async def logout(request: Request):
    request.session.pop("user_id", None)
    _set_flash(request, "Вы вышли из системы.", "success")
    return RedirectResponse("/", status_code=303)


@router.post("/trade/account/set")
async def set_account(request: Request):
    current_user = _get_current_user(request)
    if not current_user:
        _set_flash(request, "Сначала войдите в аккаунт.", "error")
        return RedirectResponse("/", status_code=303)

    form = await request.form()
    start_capital_raw = (form.get("start_capital") or "").strip()

    try:
        start_capital = float(start_capital_raw)
    except ValueError:
        _set_flash(request, "Введите корректную сумму демо-счета.", "error")
        return RedirectResponse("/", status_code=303)

    if start_capital <= 0:
        _set_flash(request, "Сумма демо-счета должна быть больше 0.", "error")
        return RedirectResponse("/", status_code=303)

    user_id = int(current_user["id"])
    with engine.begin() as connection:
        connection.execute(delete(demo_trades_table).where(demo_trades_table.c.user_id == user_id))
        stmt = (
            update(users_table)
            .where(users_table.c.id == user_id)
            .values(start_capital=start_capital, current_capital=start_capital)
        )
        connection.execute(stmt)

    _set_flash(request, "Демо-счет обновлен.", "success")
    return RedirectResponse("/", status_code=303)


@router.post("/trade/account/reset")
async def reset_account(request: Request):
    current_user = _get_current_user(request)
    if not current_user:
        _set_flash(request, "Сначала войдите в аккаунт.", "error")
        return RedirectResponse("/", status_code=303)

    user_id = int(current_user["id"])
    start_capital = float(current_user.get("start_capital") or 0.0)

    with engine.begin() as connection:
        connection.execute(delete(demo_trades_table).where(demo_trades_table.c.user_id == user_id))
        connection.execute(
            update(users_table)
            .where(users_table.c.id == user_id)
            .values(current_capital=start_capital)
        )

    _set_flash(request, "Результаты демоторговли сброшены.", "success")
    return RedirectResponse("/", status_code=303)


@router.post("/trade/{metal_key}/execute")
async def execute_trade(request: Request, metal_key: str):
    current_user = _get_current_user(request)
    if not current_user:
        _set_flash(request, "Сначала войдите в аккаунт.", "error")
        return RedirectResponse(f"/{metal_key}", status_code=303)

    metals = {
        "gold": gold_cost_table,
        "silver": silver_cost_table,
        "cupp": copper_cost_table,
    }
    if metal_key not in metals:
        _set_flash(request, "Неизвестный инструмент.", "error")
        return RedirectResponse("/", status_code=303)

    form = await request.form()
    side = (form.get("side") or "").strip().lower()
    quantity_raw = (form.get("quantity") or "").strip()

    if side not in {"buy", "sell"}:
        _set_flash(request, "Выберите тип сделки: buy или sell.", "error")
        return RedirectResponse(f"/{metal_key}", status_code=303)

    try:
        quantity = float(quantity_raw)
    except ValueError:
        _set_flash(request, "Количество должно быть числом.", "error")
        return RedirectResponse(f"/{metal_key}", status_code=303)

    if quantity <= 0:
        _set_flash(request, "Количество должно быть больше 0.", "error")
        return RedirectResponse(f"/{metal_key}", status_code=303)

    price = fetch_latest_close_price(metals[metal_key])
    total = round(price * quantity, 2)
    user_id = int(current_user["id"])

    with engine.begin() as connection:
        user_stmt = select(users_table).where(users_table.c.id == user_id).limit(1)
        user = connection.execute(user_stmt).mappings().first()
        if not user:
            _set_flash(request, "Пользователь не найден.", "error")
            return RedirectResponse(f"/{metal_key}", status_code=303)

        current_capital = float(user.get("current_capital") or 0.0)

        trade_rows_stmt = select(
            demo_trades_table.c.side,
            demo_trades_table.c.quantity,
        ).where(
            (demo_trades_table.c.user_id == user_id) & (demo_trades_table.c.metal_key == metal_key)
        )
        trade_rows = connection.execute(trade_rows_stmt).mappings().all()

        position_quantity = 0.0
        for row in trade_rows:
            if row.get("side") == "buy":
                position_quantity += float(row.get("quantity") or 0.0)
            elif row.get("side") == "sell":
                position_quantity -= float(row.get("quantity") or 0.0)

        if side == "buy":
            if total > current_capital:
                _set_flash(request, "Недостаточно средств на демо-счете.", "error")
                return RedirectResponse(f"/{metal_key}", status_code=303)
            new_capital = round(current_capital - total, 2)
        else:
            if quantity > position_quantity:
                _set_flash(request, "Нельзя продать больше, чем есть в позиции.", "error")
                return RedirectResponse(f"/{metal_key}", status_code=303)
            new_capital = round(current_capital + total, 2)

        connection.execute(
            insert(demo_trades_table).values(
                user_id=user_id,
                metal_key=metal_key,
                side=side,
                quantity=quantity,
                price=price,
                total=total,
                created_at=datetime.now(),
            )
        )
        connection.execute(
            update(users_table)
            .where(users_table.c.id == user_id)
            .values(current_capital=new_capital)
        )

    _set_flash(request, "Сделка выполнена.", "success")
    return RedirectResponse(f"/{metal_key}", status_code=303)


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
