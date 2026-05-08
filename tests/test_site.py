from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Ensure project root is on sys.path so `app` package can be imported
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app.main as app_main
import app.routes.general as general


def _stub_fetch_candles(*args, **kwargs):
    return []


def _stub_fetch_predict_candles(*args, **kwargs):
    return []


def _stub_get_current_user(request=None):
    return None


def _stub_fetch_news(*args, **kwargs):
    return []


def _stub_fetch_latest_close_price(*args, **kwargs):
    return 0.0


def _stub_run_update():
    return {"status": "ok", "inserted": 0}


def _stub_run_predictions():
    return {"status": "ok", "predictions": 0}


def test_get_pages_ok(monkeypatch):
    # Mock data access and heavy operations to make endpoints deterministic
    monkeypatch.setattr(general, "fetch_candles", _stub_fetch_candles)
    monkeypatch.setattr(general, "fetch_predict_candles", _stub_fetch_predict_candles)
    monkeypatch.setattr(general, "_get_current_user", _stub_get_current_user)
    monkeypatch.setattr(general, "fetch_news", _stub_fetch_news)
    monkeypatch.setattr(general, "fetch_latest_close_price", _stub_fetch_latest_close_price)

    client = TestClient(app_main.app)

    for path in ["/", "/gold", "/silver", "/cupp"]:
        resp = client.get(path)
        assert resp.status_code == 200, f"GET {path} returned {resp.status_code}"


def test_api_update_and_run_predictions(monkeypatch):
    # Mock the heavy update/prediction routines imported in the module
    monkeypatch.setattr(general, "update_all_data", _stub_run_update)
    monkeypatch.setattr(general, "run_price_predictions", _stub_run_predictions)

    client = TestClient(app_main.app)

    resp = client.post("/api/update-data")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"

    resp2 = client.post("/api/run-predictions")
    assert resp2.status_code == 200
    assert resp2.json().get("status") == "ok"


