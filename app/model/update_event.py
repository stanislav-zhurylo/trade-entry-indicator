from app.enums import EventType, MarketType, TimeFrame

class UpdateEvent:
    def __init__(
        self, 
        event_type: EventType, 
        market_type: MarketType = None, 
        symbol: str = None, 
        interval: TimeFrame = None
    ):
        self.event_type = event_type
        self.market_type = market_type
        self.symbol = symbol
        self.interval = interval

    @staticmethod
    def create_update_event(
        event_type: EventType, 
        market_type: MarketType, 
        symbol: str = None, 
        interval: TimeFrame = None
    ):
        """
        Static constructor method that returns an instance of UpdateEvent.
        """
        return UpdateEvent(event_type, market_type, symbol, interval)

    def __str__(self):
        return f"UpdateEvent(event_type={self.event_type}, market_type={self.market_type}, symbol={self.symbol}, interval={self.interval})"
