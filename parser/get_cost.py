import os
from dotenv import load_dotenv

load_dotenv()

from datetime import timedelta, datetime

from tinkoff.invest import CandleInterval, Client, HistoricCandle
from tinkoff.invest.schemas import CandleSource, FindInstrumentResponse
from tinkoff.invest.utils import now
from typing import List, TypedDict


TOKEN = os.getenv('INVEST_TOKEN')

class CandleDict(TypedDict):
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class VolumeDict(TypedDict):
    date: datetime
    volume: int

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
                           'volume': int(candle.volume),
                           })
    return all_candle

def list_to_volume_dict(arr: List[HistoricCandle]) -> List[VolumeDict]:
    '''Функция для перевода массива свечей в словарь объёма'''
    all_candle = []
    for candle in arr:
        all_candle.append({'date': candle.time,
                           'volume': int(candle.volume),
                           })
    return all_candle

def _get_candles(figi: str, delta: timedelta) -> List[HistoricCandle]:
    '''Общий helper для получения свечей'''

    with Client(TOKEN) as client:
        all_candle = []
        for candle in client.get_all_candles(
                instrument_id=figi,
                from_=now() - delta,
                interval=CandleInterval.CANDLE_INTERVAL_DAY,
                candle_source_type=CandleSource.CANDLE_SOURCE_UNSPECIFIED,
        ):
            all_candle.append(candle)

    return all_candle

def get_cost(figi: str) -> List[CandleDict]:
    '''Функция для получения цены по figi'''

    return list_to_dict(_get_candles(figi, timedelta(days=365 * 7)))

def get_cost_hours(figi: str) -> List[CandleDict]:
    '''Функция для получения цены по figi'''

    return list_to_dict(_get_candles(figi, timedelta(hours=1)))

def get_volume(figi: str) -> List[VolumeDict]:
    '''Функция для получения объёма торгов по figi'''

    return list_to_volume_dict(_get_candles(figi, timedelta(days=365 * 7)))

def get_volume_hours(figi: str) -> List[VolumeDict]:
    '''Функция для получения объёма торгов по figi за час'''

    return list_to_volume_dict(_get_candles(figi, timedelta(hours=1)))

if __name__ == "__main__":
    # arr = get_cost('BBG000VJ5YR4')
    # print(arr)
    # arr = get_cost_hours('BBG000VJ5YR4')
    # print(arr)
    # arr = get_volume('BBG000VJ5YR4')
    # print(arr)
    print(find('FUTCOPPE0326'))