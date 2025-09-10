import asyncio
import pyjq

from urllib.parse import urlencode
from aiocache import cached
from aiohttp import hdrs
from decimal import Decimal

from utils import execute_rest_call, unix_millis, previous_moment
from enums import MarketType, TimeFrame
from typing import Tuple, Dict

EXP_FILTER_QUOTE_VOLUME_GE = lambda value: f"map(select(.quoteVolume | tonumber >= {value}))"

async def fetch_symbols(
    min_quote_volume_futures: int = 0, 
    min_quote_volume_spot: int = 0,
) -> list[str]:
    markets = [MarketType.FUTURES, MarketType.SPOT]
    tasks = [
        execute_rest_call(hdrs.METH_GET, f"{__build_uri_base(market_type)}/ticker/24hr") 
        for market_type in markets
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    market_symbols = {}
    for market, result in zip(markets, results):
        market_symbols[market] = pyjq.first(
            f"""
            {EXP_FILTER_QUOTE_VOLUME_GE(min_quote_volume_futures if market == MarketType.FUTURES else min_quote_volume_spot) + ' | '} 
            sort_by(.symbol) | 
            map(.symbol)
            """, 
            result
        )
    futures_symbols = list(market_symbols[MarketType.FUTURES])
    spot_symbols = set(market_symbols[MarketType.SPOT])
    return list(filter(lambda symbol: symbol in spot_symbols, futures_symbols))

async def fetch_ohlc_data(
    market: MarketType, 
    symbols: list[str], 
    intervals: list[TimeFrame], 
    limit=25
):
    tasks = []
    base_url = f"{__build_uri_base(market)}/klines"
    for symbol in symbols:
        for interval in intervals:
            params = {
                'symbol': symbol,
                'interval': interval.value,
                'endTime': unix_millis(previous_moment(interval)),
                'limit': limit
            }
            tasks.append(
                execute_rest_call(
                    method=hdrs.METH_GET, 
                    url=f"{base_url}?{urlencode(params)}", 
                    payload=params
                ) 
            )
    results = await asyncio.gather(*tasks, return_exceptions=True)
    print(results)
    return [];

def __build_uri_base(marketType: MarketType) -> str:
    if MarketType.FUTURES == marketType:
        return 'https://fapi.binance.com/fapi/v1'
    else:
        return 'https://api.binance.com/api/v3'