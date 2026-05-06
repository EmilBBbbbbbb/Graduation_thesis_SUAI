"""Gold price forecasting pipeline using the saved LSTM bundle.

Run as a module:

	python -m predict_model.LSTM

The script reads gold prices and news from the database, rebuilds the feature
set expected by the saved LSTM bundle, forecasts the next horizon, and writes
the predicted candles into `gold_predict_cost`.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sqlalchemy import delete, insert
from tensorflow.keras.models import model_from_json

from db.core import table_to_df
from db.create_db import engine
from db.models import (
	gold_cost_predict_table,
	silver_cost_predict_table,
	copper_cost_predict_table,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SVM_PATH = PROJECT_ROOT / "predict_model" / "models" / "svm_sentiment_pipeline.pkl"

# map metal key to DB predict table variable
PREDICT_TABLES = {
	"gold": gold_cost_predict_table,
	"sliver": silver_cost_predict_table,
	"copper": copper_cost_predict_table,
}


def load_bundle(bundle_path: Path) -> dict:
	if not bundle_path.exists():
		raise FileNotFoundError(f"LSTM bundle not found: {bundle_path}")

	with bundle_path.open("rb") as f:
		bundle = pickle.load(f)

	required_keys = {
		"model_json",
		"model_weights",
		"x_scaler",
		"y_scaler",
		"timesteps",
		"horizon",
		"feature_columns",
		"target_columns",
	}
	missing = sorted(required_keys - set(bundle))
	if missing:
		raise KeyError(f"Bundle is missing required keys: {missing}")

	return bundle


def _normalize_dates(series: pd.Series) -> pd.Series:
	return pd.to_datetime(series).dt.floor("D")


def _compute_price_features(df: pd.DataFrame) -> pd.DataFrame:
	df = df.copy()
	df["hl_range"] = df["high"] - df["low"]
	df["oc_change"] = df["close"] - df["open"]
	df["close_return"] = df["close"].pct_change().replace([np.inf, -np.inf], 0).fillna(0)
	df["close_return_3"] = df["close"].pct_change(3).replace([np.inf, -np.inf], 0).fillna(0)
	df["close_return_5"] = df["close"].pct_change(5).replace([np.inf, -np.inf], 0).fillna(0)
	df["ma_close_5"] = df["close"].rolling(5).mean()
	df["ma_close_10"] = df["close"].rolling(10).mean()
	df["ma_close_20"] = df["close"].rolling(20).mean()
	df["volatility_5"] = df["close"].pct_change().rolling(5).std()
	df["volatility_10"] = df["close"].pct_change().rolling(10).std()
	df["price_momentum_5"] = df["close"].pct_change(5).replace([np.inf, -np.inf], 0).fillna(0)
	df["price_momentum_10"] = df["close"].pct_change(10).replace([np.inf, -np.inf], 0).fillna(0)
	return df


def load_market_data(metal: str, history_years: int = 2) -> pd.DataFrame:
	"""Load candles and news for `metal` from DB and build the model input frame.

	metal should be one of: 'gold', 'sliver', 'copper'.
	"""

	df_cost = table_to_df(f"{metal}_cost")
	if df_cost.empty:
		raise ValueError(f"{metal}_cost table is empty")

	df_cost = df_cost.copy()
	df_cost["date"] = _normalize_dates(df_cost["date"])
	df_cost = df_cost.sort_values("date").groupby("date", as_index=False).agg(
		{"open": "mean", "high": "mean", "low": "mean", "close": "mean", "volume": "mean"}
	)
	df_cost["volume"] = df_cost["volume"].fillna(0)

	if history_years is not None:
		max_cost_date = pd.to_datetime(df_cost["date"].max())
		cutoff_date = (max_cost_date - pd.DateOffset(years=history_years)).normalize()
		df_cost = df_cost[df_cost["date"] >= cutoff_date].copy()

	df_cost = _compute_price_features(df_cost)

	try:
		df_news = table_to_df(f"{metal}_news")
	except Exception:
		df_news = pd.DataFrame(columns=["date", "full_text"])

	if not df_news.empty:
		df_news = df_news.copy()
		df_news["date"] = _normalize_dates(df_news["date"])
		if history_years is not None:
			df_news = df_news[pd.to_datetime(df_news["date"]) >= df_cost["date"].min()].copy()

		svm_pipeline = joblib.load(SVM_PATH)
		df_news = df_news.dropna(subset=["full_text"]).copy()
		sentiments = svm_pipeline.predict(df_news["full_text"].astype(str))
		sentiment_map = {0: -1, 1: 0, 2: 1}
		df_news["sentiment"] = pd.Series(sentiments, index=df_news.index).map(sentiment_map).astype(int)

		daily_sentiment = df_news.groupby("date", as_index=False)["sentiment"].sum()
		daily_sentiment["sentiment"] = daily_sentiment["sentiment"].clip(-1, 1)
	else:
		daily_sentiment = pd.DataFrame({"date": df_cost["date"], "sentiment": 0})

	df = pd.merge(df_cost, daily_sentiment, on="date", how="left")
	df["sentiment"] = df["sentiment"].fillna(0).astype(int)
	df["sentiment_ma_3"] = df["sentiment"].rolling(3).mean()
	df["sentiment_ma_7"] = df["sentiment"].rolling(7).mean()
	df["price_momentum_5"] = df["close"].pct_change(5).replace([np.inf, -np.inf], 0).fillna(0)
	df["price_momentum_10"] = df["close"].pct_change(10).replace([np.inf, -np.inf], 0).fillna(0)

	fill_cols = [
		"ma_close_5",
		"ma_close_10",
		"ma_close_20",
		"volatility_5",
		"volatility_10",
		"sentiment_ma_3",
		"sentiment_ma_7",
	]
	df[fill_cols] = df[fill_cols].bfill().ffill().fillna(0)
	df = df.sort_values("date").set_index("date")
	return df


def build_model(bundle: dict):
	model = model_from_json(bundle["model_json"])
	model.set_weights(bundle["model_weights"])
	return model


def prepare_latest_window(df: pd.DataFrame, feature_columns: Iterable[str], timesteps: int, x_scaler) -> np.ndarray:
	missing_columns = [c for c in feature_columns if c not in df.columns]
	if missing_columns:
		raise KeyError(f"Missing required feature columns: {missing_columns}")

	if len(df) < timesteps:
		raise ValueError(f"Not enough rows to build a sequence: need {timesteps}, got {len(df)}")

	x_scaled = x_scaler.transform(df[list(feature_columns)])
	return np.asarray([x_scaled[-timesteps:]], dtype=np.float32)


def forecast_prices_for_metal(bundle: dict, df: pd.DataFrame) -> pd.DataFrame:
	model = build_model(bundle)
	x_scaler = bundle["x_scaler"]
	y_scaler = bundle["y_scaler"]
	timesteps = int(bundle["timesteps"])
	horizon = int(bundle["horizon"])
	feature_columns = list(bundle["feature_columns"])
	target_columns = list(bundle["target_columns"])
	num_targets = len(target_columns)

	X = prepare_latest_window(df, feature_columns, timesteps, x_scaler)
	pred_scaled = model.predict(X, verbose=0)
	pred_relative = y_scaler.inverse_transform(pred_scaled.reshape(-1, num_targets)).reshape(horizon, num_targets)

	base_prices = df[target_columns].iloc[-1].astype(float).to_numpy()
	predicted_prices = base_prices[None, :] * (1.0 + pred_relative)

	future_dates = pd.bdate_range(start=pd.Timestamp(df.index[-1]) + pd.offsets.BDay(1), periods=horizon)
	forecast_df = pd.DataFrame(predicted_prices, columns=target_columns)
	forecast_df.insert(0, "date", future_dates)
	return forecast_df


def replace_predictions_in_db(predictions: pd.DataFrame, predict_table) -> None:
	records = predictions.copy()
	records["date"] = pd.to_datetime(records["date"]).map(lambda value: pd.Timestamp(value).to_pydatetime())
	payload = records.to_dict(orient="records")
	dates = [row["date"] for row in payload]

	with engine.begin() as connection:
		connection.execute(delete(predict_table).where(predict_table.c.date.in_(dates)))
		connection.execute(insert(predict_table), payload)


def main() -> None:
	metals = ["gold", "sliver", "copper"]
	for metal in metals:
		bundle_path = PROJECT_ROOT / "predict_model" / "models" / f"{metal}_lstm_bundle.pkl"
		logger.info("Loading saved LSTM bundle for {}...", metal)
		if not bundle_path.exists():
			logger.warning("Bundle for %s not found, skipping", metal)
			continue

		with bundle_path.open("rb") as f:
			bundle = pickle.load(f)

		history_years = int(bundle.get("history_years", 2))

		logger.info("Loading %s market data from database...", metal)
		try:
			market_df = load_market_data(metal, history_years=history_years)
		except Exception as e:
			logger.error("Failed to load market data for %s: %s", metal, e)
			continue

		logger.info("Forecasting %s prices...", metal)
		forecast_df = forecast_prices_for_metal(bundle, market_df)

		predict_table = PREDICT_TABLES.get(metal)
		if predict_table is None:
			logger.warning("No predict table configured for %s, skipping DB write", metal)
			print(forecast_df.to_string(index=False))
			continue

		logger.info("Saving predictions to database table %s...", predict_table.name)
		replace_predictions_in_db(forecast_df, predict_table)
		logger.info("Predictions for %s saved successfully.", metal)
		print(f"--- {metal.upper()} predictions ---")
		print(forecast_df.to_string(index=False))

	logger.info("All done.")


if __name__ == "__main__":
	main()



