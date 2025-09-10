from app.model import UpdateEvent
from app.enums import MarketType, TimeFrame, EventType, MessageType

def __parse_candles(
    market: MarketType, 
    symbol: str, 
    interval: TimeFrame, 
    message: list, 
    model: dict
) -> UpdateEvent:
    for _, item in enumerate(message):
        timestamp = item[0]
        candle = model['ohlc'][market.value][symbol][interval.value][timestamp]
        candle['open'] = item[1]
        candle['high'] = item[2]
        candle['low'] = item[3]
        candle['close'] = item[4]
    return UpdateEvent.create_update_event(
        EventType.CANDLE_UPDATE, 
        market, 
        symbol, 
        interval
    )

def process_message(
    type: MessageType,
    market: MarketType, 
    symbol: str, 
    interval: TimeFrame, 
    message, 
    model: dict
) -> UpdateEvent: 
    if type == MessageType.CANDLE_HISTORY:
        return __parse_candles(market, symbol, interval, message, model)
    raise ValueError(f"Unsupported message type {type}")
    