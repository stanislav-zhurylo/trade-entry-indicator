from enum import Enum

class EventType(Enum):
    CANDLE_UPDATE = 'CANDLE_UPDATE'
    SYMBOL_UPDATE = 'SYMBOL_UPDATE'
    METRIC_UPDATE = 'METRIC_UPDATE'
    CANDLE_CLEANUP = 'CANDLE_CLEANUP'
    
    def __str__(self):
        return self.value