from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime

with DAG(
        dag_id='test_investments_db',
        start_date=datetime(2024, 1, 1),
        schedule_interval=None,
        catchup=False
) as dag:
    test_connection = PostgresOperator(
        task_id='test_connection',
        postgres_conn_id='investments_db',
        sql='SELECT 1 as test;'
    )