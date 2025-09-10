from enum import Enum

class MessageType(Enum):
    CANDLE_HISTORY = 'CANDLE_HISTORY'
    
    def __str__(self):
        return self.value