from db.create_db import engine
from parser.get_cost import get_cost, list_to_dict
from sqlalchemy import Table
from sqlalchemy import insert
import pandas as pd

def insert_data(id: str, table: Table)->None:
    with engine.connect() as connection:
        candles = get_cost(id)
        stmt = insert(table).values(list_to_dict(candles))
        connection.execute(stmt)
        connection.commit()

def drop_table(table: Table)->None:
    with engine.connect() as connection:
        table.drop(connection)
        connection.commit()

def drop_all_tables(tables: list[Table])->None:
    with engine.connect() as connection:
        for table in tables:
            table.drop(connection)
        connection.commit()

def table_to_df(table_name: str)->pd.DataFrame:
    with engine.connect() as connection:
        df = pd.read_sql(table_name, con=connection)
        return df

if __name__ == '__main__':
    pass