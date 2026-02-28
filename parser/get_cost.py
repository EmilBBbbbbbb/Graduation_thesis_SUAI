import os
from dotenv import load_dotenv

load_dotenv()

from datetime import timedelta, datetime

from tinkoff.invest import CandleInterval, Client, HistoricCandle
from tinkoff.invest.schemas import CandleSource, FindInstrumentResponse
from tinkoff.invest.utils import now
from typing import List, TypedDict


TOKEN = os.getenv('INVEST_TOKEN')

import sys
from loguru import logger

class CandleDict(TypedDict):
    date: datetime
    open: float
    high: float
    low: float
    close: float

def find(name: str) -> FindInstrumentResponse:
    '''Функция для поиска по необходимого актива'''

    with Client(token=TOKEN) as client:
        return client.instruments.find_instrument(query=name)

def list_to_dict(arr: List[HistoricCandle]) -> List[CandleDict]:
    '''Функция для перевода массива в словарь'''
    all_candle = []
    for candle in arr:
        all_candle.append({'date': candle.time,
                           'open': float(f'{candle.open.units}.{candle.open.nano}'),
                           'high': float(f'{candle.high.units}.{candle.high.nano}'),
                           'low': float(f'{candle.low.units}.{candle.low.nano}'),
                           'close': float(f'{candle.close.units}.{candle.close.nano}'),
                           })
    return all_candle

def get_cost(figi: str) -> List[CandleDict]:
    '''Функция для получения цены по figi'''

    with Client(TOKEN) as client:
        all_candle = []
        for candle in client.get_all_candles(
                instrument_id=figi,
                from_=now() - timedelta(days=365 * 7),
                interval=CandleInterval.CANDLE_INTERVAL_DAY,
                candle_source_type=CandleSource.CANDLE_SOURCE_UNSPECIFIED,
        ):
            all_candle.append(candle)

    return list_to_dict(all_candle)

def get_cost_hours(figi: str) -> List[CandleDict]:
    '''Функция для получения цены по figi'''

    with Client(TOKEN) as client:
        all_candle = []
        for candle in client.get_all_candles(
                instrument_id=figi,
                from_=now() - timedelta(hours=1),
                interval=CandleInterval.CANDLE_INTERVAL_DAY,
                candle_source_type=CandleSource.CANDLE_SOURCE_UNSPECIFIED,
        ):
            all_candle.append(candle)

    return list_to_dict(all_candle)

if __name__ == "__main__":
    # arr = get_cost('BBG000VJ5YR4')
    # print(arr)
    # arr = get_cost_hours('BBG000VJ5YR4')
    # print(arr)
    print(find('FUTCOPPE0326'))