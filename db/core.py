from db.create_db import engine
from parser.get_cost import get_cost, CandleDict
from sqlalchemy import Table
from sqlalchemy import insert
import pandas as pd

from scraper.scrape import NewsDict, Scraper
from db.models import (
    gold_cost_table,
    silver_cost_table,
    copper_cost_table,
    gold_news_table,
    silver_news_table,
    copper_news_table,
)

from typing import List

import sys
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")

def insert_data(data: List[CandleDict|NewsDict], table: Table)->None:
    '''Вставка данных в таблицу'''

    with engine.connect() as connection:
        stmt = insert(table).values(data)
        connection.execute(stmt)
        connection.commit()

    logger.info('Данные вставлены в таблицу {}.'.format(table.name))

def drop_table(table: Table)->None:
    '''Удаление таблицы'''

    with engine.connect() as connection:
        table.drop(connection)
        connection.commit()

def drop_all_tables(tables: List[Table])->None:
    '''Удаление всех таблиц'''

    with engine.connect() as connection:
        for table in tables:
            table.drop(connection)
        connection.commit()

    logger.info('Все таблицы удалены.')

def table_to_df(table_name: str)->pd.DataFrame:
    '''Чтение таблицы в DataFrame'''

    with engine.connect() as connection:
        df = pd.read_sql(table_name, con=connection)
        return df

def filling_all_tables()->None:
    '''Заполнение всех таблиц'''

    logger.info('Заполнение всех таблиц...')
    # Заполнение таблицы стоимости золота
    gold_cost = get_cost('BBG000VJ5YR4')
    insert_data(gold_cost, gold_cost_table)
    logger.info('Заполнена таблица стоимости золота.')

    # Заполнение таблицы стоимости серебра
    silver_cost = get_cost('BBG000VHQTD1')
    insert_data(silver_cost, silver_cost_table)
    logger.info('Заполнена таблица стоимости серебра.')

    # Заполнение таблицы стоимости меди
    copper_cost = get_cost('FUTCOPPE0326')
    insert_data(copper_cost, copper_cost_table)
    logger.info('Заполнена таблица стоимости меди.')

    gold_scraper = Scraper(
        url='https://www.finversia.ru/dragmetally',
        keywords=['золот', 'gold'],
        output_file=False,
        years=5,
        max_pages=200
    )
    silver_scraper = Scraper(
        url='https://www.finversia.ru/dragmetally',
        keywords=['серебр', 'silver'],
        output_file=False,
        years=5,
        max_pages=200
    )
    copper_scraper = Scraper(
        url='https://www.finversia.ru/syrevye-rynki',
        keywords=['мед', 'copper'],
        output_file=False,
        years=5,
        max_pages=200
    )

    # Заполнение таблицы новостей о золоте
    insert_data(gold_scraper.parsing(), gold_news_table)
    logger.info('Заполнена таблица новостей о золоте.')

    # Заполнение таблицы новостей о серебре
    insert_data(silver_scraper.parsing(), silver_news_table)
    logger.info('Заполнена таблица новостей о серебре.')

    # Заполнение таблицы новостей о меде
    insert_data(copper_scraper.parsing(), copper_news_table)
    logger.info('Заполнена таблица новостей о меди.')


if __name__ == '__main__':
    # drop_all_tables([
    #     gold_cost_table,
    #     silver_cost_table,
    #     copper_cost_table,
    #     gold_news_table,
    #     silver_news_table,
    #     copper_news_table])
    filling_all_tables()