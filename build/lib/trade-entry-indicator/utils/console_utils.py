import pandas as pd

from enums import MarketType

def print_order_book(storage: dict):
    bids = pd.DataFrame(storage['bids'].items(), columns=['Price', 'Quantity'])
    asks = pd.DataFrame(storage['asks'].items(), columns=['Price', 'Quantity'])
    
    print("Bids:")
    print(bids.sort_values(by='Price', ascending=False).head(5))
    
    print("Asks:")
    print(asks.sort_values(by='Price').head(5))