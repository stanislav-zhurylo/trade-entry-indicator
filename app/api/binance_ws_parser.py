import asyncio
import pyjq
import json

from urllib.parse import urlencode
from aiocache import cached
from aiohttp import hdrs
from decimal import Decimal

from app.model import UpdateEvent
from app.utils import unix_millis, previous_moment
from app.enums import MarketType, TimeFrame, EventType
from typing import Callable, Tuple, Dict

STREAM_KLINE: Callable[[str, TimeFrame], str] = lambda symbol, interval: f"{symbol.lower()}@kline_{interval.value}"

def __parse_candles(
    market: MarketType, 
    data: dict, 
    model: dict
) -> UpdateEvent:
    symbol = data.get("s", None)
    interval = data.get("i", None)
    timestamp = data.get("t", None)
    open = data.get("o", None);
    high = data.get("h", None);
    close = data.get("c", None);
    low = data.get("l", None);
    candle = model['ohlc'][market.value][symbol][interval][timestamp]
    candle['open'] = open
    candle['high'] = high
    candle['low'] = low
    candle['close'] = close
    return UpdateEvent.create_update_event(
        EventType.CANDLE_UPDATE, 
        market, 
        symbol, 
        TimeFrame.from_string(interval)
    )

def process_message(market: MarketType, message: dict, model: dict) -> UpdateEvent: 
    data = message.get("data", {})
    type = data.get("e", None)
    if type == 'kline':
        return __parse_candles(market, data.get("k", {}), model)
    else:
        raise ValueError(f"Unsupported message type {type}")
    