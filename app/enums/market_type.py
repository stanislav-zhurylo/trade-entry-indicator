from enum import Enum

class MarketType(Enum):
    SPOT = 'SPOT'
    FUTURES = 'FUTURES'
    
    def __str__(self):
        return self.value