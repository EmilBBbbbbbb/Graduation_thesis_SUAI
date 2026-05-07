"""Utilities to update DB content and run predictions.

This module centralizes the update logic so it can be called from the
backend endpoints. The DAG will call the backend endpoints instead of
containing scraping/prediction logic itself.
"""

from typing import Dict, Any
import logging

from db.core import insert_data, table_to_df
from db.models import (
    gold_cost_table,
    silver_cost_table,
    copper_cost_table,
    gold_news_table,
    silver_news_table,
    copper_news_table,
)
from parser.get_cost import get_cost_daily
from scraper.scrape import Scraper
from predict_model.LSTM import main as run_predictions_main

logger = logging.getLogger(__name__)


def _update_price_table(figi: str, table) -> Dict[str, Any]:
    try:
        candles = get_cost_daily(figi)
        if candles:
            insert_data(candles, table)
            return {"inserted": len(candles)}
        return {"inserted": 0, "note": "no new candles"}
    except Exception as e:
        logger.exception("Failed to update price table %s", getattr(table, 'name', table))
        return {"error": str(e)}


def _update_news(url: str, keywords: list[str], table) -> Dict[str, Any]:
    try:
        scraper = Scraper(url=url, keywords=keywords, output_file=False, years=1, max_pages=1)
        news = scraper.get_recent_news()
        if news:
            insert_data(news, table)
            return {"inserted": len(news)}
        return {"inserted": 0, "note": "no new news"}
    except Exception as e:
        logger.exception("Failed to update news table %s", getattr(table, 'name', table))
        return {"error": str(e)}


def update_all_data() -> Dict[str, Any]:
    """Run full update: prices and news for all metals.

    Returns a summary dict with inserted counts and possible errors.
    """
    summary: dict[str, Any] = {}

    summary['gold_prices'] = _update_price_table('BBG000VJ5YR4', gold_cost_table)
    summary['silver_prices'] = _update_price_table('BBG000VHQTD1', silver_cost_table)
    summary['copper_prices'] = _update_price_table('FUTCOPPE0326', copper_cost_table)

    summary['gold_news'] = _update_news('https://www.finversia.ru/dragmetally', ['золот', 'gold'], gold_news_table)
    summary['silver_news'] = _update_news('https://www.finversia.ru/dragmetally', ['серебр', 'silver'], silver_news_table)
    summary['copper_news'] = _update_news('https://www.finversia.ru/syrevye-rynki', ['мед', 'copper'], copper_news_table)

    return summary


def run_price_predictions() -> Dict[str, Any]:
    """Run prediction routine (invokes predict_model.LSTM.main).

    Returns status dict. The prediction code writes predicted rows into DB.
    """
    try:
        run_predictions_main()
        return {"status": "ok"}
    except Exception as e:
        logger.exception("Prediction run failed")
        return {"status": "error", "error": str(e)}

