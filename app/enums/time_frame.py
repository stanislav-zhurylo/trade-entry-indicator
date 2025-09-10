from enum import Enum

class TimeFrame(Enum):
    MIN_1 = '1m'
    MIN_3 = '3m'
    MIN_5 = '5m'
    MIN_10 = '10m'
    MIN_15 = '15m'
    MIN_30 = '30m'
    HOUR_1 = '1h'
    
    @classmethod
    def from_string(cls, value: str):
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f"{value} is not a valid {cls.__name__}")
    
    def __str__(self):
        return self.value