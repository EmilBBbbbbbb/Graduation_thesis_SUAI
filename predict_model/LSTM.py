from __future__ import annotations

import argparse
import pickle
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from tensorflow.keras.models import model_from_json

# Ensure project root is importable when running as a script.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from db.create_db import engine
from db.models import gold_cost_predict_table, gold_cost_table


def load_lstm_bundle(bundle_path: Path) -> tuple[Any, Any, int, list[str]]:
	"""Загрузка модели/масштабировщика/метаданных, сохраненных в пакете pickle."""
	with bundle_path.open("rb") as file:
		bundle = pickle.load(file)

	model = model_from_json(bundle["model_json"])
	model.set_weights(bundle["model_weights"])
	model.compile(optimizer="adam", loss="mse", metrics=["mae"])

	scaler = bundle["scaler"]
	timesteps = int(bundle["timesteps"])
	columns = list(bundle["columns"])
	return model, scaler, timesteps, columns


def load_gold_history(columns: list[str]) -> pd.DataFrame:
	"""Чтение истории из базы данных в хронологическом порядке"""
	with engine.connect() as connection:
		stmt = select(gold_cost_table).order_by(gold_cost_table.c.date)
		rows = connection.execute(stmt).mappings().all()

	if not rows:
		raise ValueError("Таблица gold_cost пуста, предсказание невозможно.")

	history = pd.DataFrame(rows)
	history = history[["date", *columns]].copy()
	return history


def recursive_forecast(
	model: Any,
	scaler: Any,
	history: pd.DataFrame,
	timesteps: int,
	columns: list[str],
	horizon: int,
) -> list[dict[str, Any]]:
	if len(history) < timesteps:
		raise ValueError(
			f"Недостаточно данных для timesteps={timesteps}. "
			f"Доступно только {len(history)} строк."
		)

	values_df = history[columns].copy()
	scaled_values = scaler.transform(values_df)

	window = scaled_values[-timesteps:].copy()
	base_date = pd.to_datetime(history["date"].iloc[-1]).to_pydatetime()
	predictions: list[dict[str, Any]] = []

	for step in range(horizon):
		x_input = np.array([window], dtype=np.float32)
		pred_scaled = model.predict(x_input, verbose=0)[0]
		pred_scaled_df = pd.DataFrame([pred_scaled], columns=columns)
		pred_real = scaler.inverse_transform(pred_scaled_df)[0]

		next_date = base_date + timedelta(days=step)
		row = {"date": next_date}
		row.update({column: float(value) for column, value in zip(columns, pred_real)})
		predictions.append(row)

		# Shift forecasting window by one step and append newest prediction.
		window = np.vstack([window[1:], pred_scaled])

	return predictions


def upsert_predictions(records: list[dict[str, Any]]) -> int:
	"""Обновление предсказаний"""
	if not records:
		return 0

	stmt = pg_insert(gold_cost_predict_table).values(records)
	upsert_stmt = stmt.on_conflict_do_update(
		index_elements=[gold_cost_predict_table.c.date],
		set_={
			"open": stmt.excluded.open,
			"high": stmt.excluded.high,
			"low": stmt.excluded.low,
			"close": stmt.excluded.close,
		},
	)

	with engine.begin() as connection:
		connection.execute(upsert_stmt)

	return len(records)


def run(horizon: int = 30) -> int:
	bundle_path = Path("predict_model/models/gold_lstm_bundle.pkl")
	if not bundle_path.exists():
		raise FileNotFoundError(f"Не найден файл модели: {bundle_path}")

	model, scaler, timesteps, columns = load_lstm_bundle(bundle_path)
	history = load_gold_history(columns)
	records = recursive_forecast(model, scaler, history, timesteps, columns, horizon)
	saved = upsert_predictions(records)
	return saved


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Forecast gold prices and save to DB")
	parser.add_argument(
		"--horizon",
		type=int,
		default=30,
		help="Количество дней прогноза для записи в gold_predict_cost",
	)
	args = parser.parse_args()

	inserted = run(horizon=args.horizon)
	print(f"Сохранено прогнозов в gold_predict_cost: {inserted}")



