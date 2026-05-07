"""Lightweight DAG that triggers backend endpoints.

The heavy lifting (scraping, DB inserts, predictions) is performed by the
FastAPI backend endpoints. This DAG simply calls those endpoints on a daily
schedule.
"""

import os
import logging
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv('BACKEND_URL', 'http://host.docker.internal:8000')

default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Run daily at 00:00 UTC
SCHEDULE = '0 0 * * *'


def _call_endpoint(path: str, timeout: int = 300):
    url = f"{BACKEND_URL}{path}"
    logger.info('Calling backend: %s', url)
    resp = requests.post(url, timeout=timeout)
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        return {"status_code": resp.status_code, "text": resp.text}


def call_update_api(**_):
    return _call_endpoint('/api/update-data')


def call_predict_api(**_):
    return _call_endpoint('/api/run-predictions')


with DAG(
    dag_id='update_information_dag',
    default_args=default_args,
    schedule_interval=SCHEDULE,
    catchup=False,
    tags=['metals', 'prices', 'news', 'predictions'],
) as dag:

    task_update = PythonOperator(
        task_id='call_backend_update',
        python_callable=call_update_api,
    )

    task_predict = PythonOperator(
        task_id='call_backend_predict',
        python_callable=call_predict_api,
    )

    task_update >> task_predict
