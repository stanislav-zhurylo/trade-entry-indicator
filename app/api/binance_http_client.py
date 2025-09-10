import asyncio
import pyjq

from urllib.parse import urlencode
from aiohttp import hdrs

from app.client import execute_http_request
from app.utils import unix_millis, previous_moment
from app.enums import MarketType, TimeFrame

async def fetch_exchange_info(market: MarketType) -> dict:
    response = await execute_http_request(
        hdrs.METH_GET, 
        f"{__build_uri_base(market)}/exchangeInfo"
    ) 
    return response;

async def fetch_tickers_24h(market: MarketType) -> dict:
    response = await execute_http_request(
        hdrs.METH_GET, 
        f"{__build_uri_base(market)}/ticker/24hr"
    ) 
    return response;

async def fetch_candles(
    market: MarketType, 
    symbol: str, 
    interval: TimeFrame, 
    limit=25
) -> dict:
    base_url = f"{__build_uri_base(market)}/klines"
    params = {
        'symbol': symbol,
        'interval': interval.value,
        'endTime': unix_millis(previous_moment(interval)),
        'limit': limit
    } 
    return await execute_http_request(
        method=hdrs.METH_GET, 
        url=f"{base_url}?{urlencode(params)}",
    );

def __build_uri_base(marketType: MarketType) -> str:
    if MarketType.FUTURES == marketType:
        return 'https://fapi.binance.com/fapi/v1'
    else:
        return 'https://api.binance.com/api/v3'