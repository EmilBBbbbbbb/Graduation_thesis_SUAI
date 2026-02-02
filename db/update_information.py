import datetime as dt
import time

from scheduler import Scheduler

import sys
from loguru import logger

from db.core import insert_data
from db.models import gold_cost_table, silver_cost_table, copper_cost_table, gold_news_table, silver_news_table, \
    copper_news_table
from parser.get_cost import get_cost_hours

from scraper.scrape import Scraper

logger.remove()
logger.add(sys.stderr, level="DEBUG")

schedule = Scheduler()

gold_scraper = Scraper(
        url='https://www.finversia.ru/dragmetally',
        keywords=['золот', 'gold'],
        output_file=False,
        years=5,
        max_pages=1
    )
silver_scraper = Scraper(
    url='https://www.finversia.ru/dragmetally',
    keywords=['серебр', 'silver'],
    output_file=False,
    years=5,
    max_pages=1
)
copper_scraper = Scraper(
    url='https://www.finversia.ru/syrevye-rynki',
    keywords=['мед', 'copper'],
    output_file=False,
    years=5,
    max_pages=1
)

def update_information() -> None:
    '''Функция для обновления информации в базе данных'''
    logger.info('Обновление данных...')
    # Обновление таблицы стоимости золота
    gold_cost = get_cost_hours('BBG000VJ5YR4')
    if gold_cost:
        insert_data(gold_cost, gold_cost_table)
    else:
        logger.info('Нет информации о цене золоте за час')

    # Обновление таблицы стоимости серебра
    silver_cost = get_cost_hours('BBG000VHQTD1')
    if silver_cost:
        insert_data(silver_cost, silver_cost_table)
    else:
        logger.info('Нет информации о цене серебре за час')

    # Обновление таблицы стоимости меди
    copper_cost = get_cost_hours('FUTCOPPE0326')
    if copper_cost:
        insert_data(copper_cost, copper_cost_table)
    else:
        logger.info('Нет информации о цене меди за час')


    # Обновление таблицы новостей о золоте
    news_gold=gold_scraper.get_recent_news()
    if news_gold:
        insert_data(news_gold, gold_news_table)
        logger.info('Обновлена таблица новостей о золоте.')
    else:
        logger.info('Нет новых новостей о золоте')


    # Обновление таблицы новостей о серебре
    news_silver=silver_scraper.get_recent_news()
    if news_silver:
        insert_data(news_silver, silver_news_table)
        logger.info('Обновлена таблица новостей о серебре.')
    else:
        logger.info('Нет новых новостей о серебре')


    # Обновление таблицы новостей о меде
    news_copper=copper_scraper.get_recent_news()
    if news_copper:
        insert_data(news_copper, copper_news_table)
        logger.info('Обновлена таблица новостей о меди.')
    else:
        logger.info('Нет новых новостей о меди')


schedule.cyclic(dt.timedelta(hours=1), update_information)

if __name__ == '__main__':
    #print(silver_scraper.get_recent_news())
    while True:
        schedule.exec_jobs()
        time.sleep(1)