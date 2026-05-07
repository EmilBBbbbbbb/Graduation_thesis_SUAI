"""Manual DAG that mirrors `update_information_dag` but runs only on trigger.

It calls backend endpoints for:
1) updating prices/news
2) running predictions

No schedule is configured, so this DAG is executed only manually from Airflow.
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


def _call_endpoint(path: str, timeout: int = 300):
    url = f"{BACKEND_URL}{path}"
    logger.info('Calling backend endpoint: %s', url)
    resp = requests.post(url, timeout=timeout)
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        return {"status_code": resp.status_code, "text": resp.text}


def _call_update(timeout: int = 300):
    return _call_endpoint('/api/update-data', timeout=timeout)


def _call_predict(timeout: int = 300):
    return _call_endpoint('/api/run-predictions', timeout=timeout)


with DAG(
    dag_id='update_information_manual',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=['metals', 'manual', 'update'],
) as dag:

    task_update = PythonOperator(
        task_id='call_backend_update',
        python_callable=_call_update,
    )

    task_predict = PythonOperator(
        task_id='call_backend_predict',
        python_callable=_call_predict,
    )

    task_update >> task_predict

