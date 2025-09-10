import asyncio
import argparse
import websockets
import pandas as pd
import numpy as np
import json
import ccxt
import time
import threading
import traceback
import sys
import os

from playsound import playsound
from datetime import datetime
from flask import Flask, jsonify, request
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

from app.model import UpdateEvent
from app.client.websocket_client import WebSocketClient
from app.enums import MarketType, TimeFrame, MessageType, EventType
from app.utils import nested_dict, \
    run_until_complete, \
    handle_task_result, \
    seconds, previous_moment
        
from app.api import fetch_tickers_24h, \
    fetch_candles, \
    process_http_message, \
    process_ws_message, \
    STREAM_KLINE
    
    
# Initialize exchanges
bybit = ccxt.bybit()
okx = ccxt.okx()

# Define percent threshold
THRESHOLD = 0.002  # 0.4%

app = Flask(__name__)

model = {
    "config": {
        "max_candles": 50
    },
    "symbols": [],
    "intervals": [
        TimeFrame.MIN_1, 
        TimeFrame.MIN_5
    ],
    "ohlc": nested_dict(),
    "metrics": nested_dict(),
    "last_prices": nested_dict(),
    "notifications": nested_dict(),
}

def __fetch_symbols(market_type: MarketType):
    global model 
    tasks = [
        fetch_tickers_24h(market_type) 
    ]
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(asyncio.gather(*tasks)) 
    usdt_pairs = [ticker for ticker in results[0] if ticker["symbol"].endswith("USDT")]
    
    #usdt_pairs = results[0]
    
    # Compute quote volume in float
    for ticker in usdt_pairs: ticker["quoteVolume"] = float(ticker["quoteVolume"])
    
    # Sort by quoteVolume (24h traded volume in quote asset, e.g. USDC)
    sorted_by_volume = sorted(usdt_pairs, key=lambda x: x["quoteVolume"], reverse=True)[:400]

    model['symbols'] = [
        ticker['symbol'] for ticker in sorted_by_volume
    ]
    
    model['symbols'] = model['symbols']
    
    print(model['symbols']) 

async def __fetch_candles(market: MarketType):
    global model
    max_candles = model['config']['max_candles']
    
    symbols = model['symbols']
    errored_symbols = set()
    
    print(f"Loading historical candle data for {len(symbols)} symbols")
    
    i = 0
    for symbol in symbols:
        for interval in model['intervals']:
            try:
                data = await fetch_candles(
                    market, 
                    symbol, 
                    interval, 
                    limit=max_candles
                )
                update_event = process_http_message(
                    MessageType.CANDLE_HISTORY, 
                    market, 
                    symbol, 
                    interval, 
                    data, 
                    model
                )
                cleanup_event = execute_candle_history_cleanup(
                    update_event.event_type,
                    update_event.market_type,
                    update_event.symbol,
                    update_event.interval,
                )
            
            except Exception as e:
                errored_symbols.add(symbol)

            await asyncio.sleep(0.01)
            
        percentage = ((i + 1) / len(symbols)) * 100
            
        #print(f"({i + 1}/{len(symbols)}, {percentage:.2f}%) {symbol}: Historical OHLC data loaded w/ {'ERROR' if symbol in errored_symbols else 'SUCCESS'}")  
        i += 1
            
    print(f"OHLC buffer loading complete: ({len(symbols) - len(errored_symbols)} OK, {len(errored_symbols)} NOK, {len(symbols)} TOTAL)")
 
def __ws_connection_reset(market_type: MarketType):
    global model
    streams = [
        STREAM_KLINE(symbol, timeframe)
        for symbol in model['symbols'] 
        for timeframe in model['intervals']
    ]
    uri = f"wss://fstream.binance.com/stream?streams={'/'.join(streams)}"
    print(f"Connecting to {(uri[:47] + '...') if len(uri) > 50 else uri} to listen {len(streams)} websocket streams")
    client = WebSocketClient(uri, lambda message: __ws_message_received(message, market_type))
    client.restart()
        
def __ws_message_received(message, market_type: MarketType):
    data = json.loads(message)
    update_event = process_ws_message(
        market_type, 
        data, 
        model
    )
    cleanup_event = execute_candle_history_cleanup(
        update_event.event_type,
        update_event.market_type,
        update_event.symbol,
        update_event.interval
    )
    calculate_bb_metrics(
        update_event.market_type,
        update_event.symbol,
        update_event.interval
    )

def calculate_bb_metrics(
    market: MarketType,
    symbol: str,
    interval: TimeFrame):
    global model
    
    max_candles = model['config']['max_candles']
    ohlc_data = model['ohlc'][market.value][symbol][interval.value]
    
    if (len(ohlc_data) >= max_candles):
        
        close_prices = [ohlc_data[key]['close'] for key in ohlc_data]

        # Convert to pandas Series for easier calculations
        close_series = pd.Series(close_prices)

        # Step 2: Set the period and standard deviation factor for Bollinger Bands
        window = 20  # Rolling window for moving average
        std_dev_factor = 2  # Typically, Bollinger Bands use 2 standard deviations

        # Step 3: Calculate the Simple Moving Average (SMA)
        sma = close_series.rolling(window=window).mean()

        # Step 4: Calculate the rolling standard deviation
        rolling_std = close_series.rolling(window=window).std()

        # Step 5: Calculate Bollinger Bands
        upper_band = sma + (rolling_std * std_dev_factor)
        lower_band = sma - (rolling_std * std_dev_factor)

        # Combine into a DataFrame for clearer presentation
        pd_bb = pd.DataFrame({
            'Close': close_series,
            'SMA': sma,
            'Upper': upper_band,
            'Lower': lower_band
        })
        
        upper_band = pd_bb['Upper'].iloc[-1]
        sma = pd_bb['SMA'].iloc[-1]
        lower_band = pd_bb['Lower'].iloc[-1]
        
        model['metrics']['bb_last_candle'][market.value][symbol][interval.value]['upper_band'] = upper_band
        model['metrics']['bb_last_candle'][market.value][symbol][interval.value]['sma'] = sma
        model['metrics']['bb_last_candle'][market.value][symbol][interval.value]['lower_band'] = lower_band
        
        latest_timestamp = max(ohlc_data.keys())
        latest_close = ohlc_data[latest_timestamp]['close']
        current_timestamp = int(previous_moment(TimeFrame.MIN_1).timestamp())
        
        close_price = latest_close
        upper_band_1m = model['metrics']['bb_last_candle'][market.value][symbol][TimeFrame.MIN_1.value]['upper_band']
        upper_band_5m = model['metrics']['bb_last_candle'][market.value][symbol][TimeFrame.MIN_5.value]['upper_band']
        lower_band_1m = model['metrics']['bb_last_candle'][market.value][symbol][TimeFrame.MIN_1.value]['lower_band']
        lower_band_5m = model['metrics']['bb_last_candle'][market.value][symbol][TimeFrame.MIN_5.value]['lower_band']
        
        close_price = float(close_price)
        upper_band_1m = float(0) if (isinstance(upper_band_1m, defaultdict) or upper_band_1m is None) else float(upper_band_1m)
        upper_band_5m = float(0) if (isinstance(upper_band_5m, defaultdict) or upper_band_5m is None) else float(upper_band_5m)
        lower_band_1m = float(0) if (isinstance(lower_band_1m, defaultdict) or lower_band_1m is None) else float(lower_band_1m)
        lower_band_5m = float(0) if (isinstance(lower_band_5m, defaultdict) or lower_band_5m is None) else float(lower_band_5m)
    
        
        dt_object = datetime.fromtimestamp(latest_timestamp / 1000)
        formatted_date = dt_object.strftime('%Y-%m-%d %H:%M')
        
        wh_1m = percentage_difference(upper_band_1m, lower_band_1m)
        wh_5m = percentage_difference(upper_band_5m, lower_band_5m)
        
        symbol_qv24h_index = model['symbols'].index(symbol) + 1
        total_symbols = len(model['symbols'])
        
        formatted_symbol = symbol
        
        notified_timestamp = model['notifications'][symbol]
        notified_timestamp = 0 if (isinstance(notified_timestamp, defaultdict) or notified_timestamp is None) else notified_timestamp
        
        if (interval == TimeFrame.MIN_1 and wh_1m > 0.02):
            if (current_timestamp != notified_timestamp):
                if (close_price > 0.0 and upper_band_1m > 0.0 and upper_band_5m > 0.0 and lower_band_1m > 0.0 and lower_band_5m > 0.0):
                    if (close_price >= upper_band_1m and close_price >= upper_band_5m):
                        play_sound_async('app/assets/wav/ringbell_001.wav')
                        print(f"({symbol_qv24h_index}/{total_symbols}) {formatted_symbol} [{formatted_date}]: SELL | WH/2: {wh_1m/2.0:.2f}% (1m), {wh_5m/2.0:.2f}% (5m)")
                        model['notifications'][symbol] = current_timestamp
                    elif (close_price <= lower_band_1m and close_price <= lower_band_5m):
                        play_sound_async('app/assets/wav/ringbell_001.wav')
                        print(f"({symbol_qv24h_index}/{total_symbols}) {formatted_symbol} [{formatted_date}]: BUY | WH/2: {wh_1m/2.0:.2f}% (1m), {wh_5m/2.0:.2f}% (5m)")
                        model['notifications'][symbol] = current_timestamp
                        
    
def percentage_difference(price1, price2):
    try:
        diff = abs(price1 - price2)
        percentage_diff = (diff / price1) * 100
        return percentage_diff
    except ZeroDivisionError:
        return "Price1 cannot be zero."    
        
def execute_candle_history_cleanup(
    previous: EventType,
    market: MarketType,
    symbol: str,
    interval: TimeFrame,
) -> UpdateEvent:
    global model
    candles = model['ohlc'][market.value][symbol][interval.value]
    max_candles = model['config']['max_candles']
    if len(candles) > max_candles:
        latest_candles = nested_dict()
        latest_timestamps = sorted(candles.keys())[-max_candles:]
        for ts in latest_timestamps:
            latest_candles[ts] = candles[ts]
        model['ohlc'][market.value][symbol][interval.value] = latest_candles
        # print(f"{symbol} {interval.value}: Cleared")
                
    return UpdateEvent.create_update_event(
        EventType.CANDLE_CLEANUP, 
        market, 
        symbol, 
        interval
    )
    
def play_sound_async(path):
    threading.Thread(target=playsound, args=(path,), daemon=True).start()
    
    
    

    
def fetch_perpetual_tickers(exchange, quote_currency):
    tickers = exchange.fetch_tickers()
    return {
        symbol.replace(':USDT', ''): data['last']
        for symbol, data in tickers.items()
        if symbol.endswith(quote_currency) and data['last'] is not None
    }

def get_common_symbols(bybit_tickers, okx_tickers):
    bybit_symbols = {s for s in bybit_tickers}
    okx_symbols = {s for s in okx_tickers}
    return bybit_symbols & okx_symbols

def compare_prices():
    print("Fetching prices...")
    bybit_tickers = fetch_perpetual_tickers(bybit, 'USDT')
    okx_tickers = fetch_perpetual_tickers(okx, 'USDT')
    
    common_symbols = get_common_symbols(bybit_tickers, okx_tickers)

    print(f"\n🔍 Comparing {len(common_symbols)} common perpetual futures...\n")

    for sym in sorted(common_symbols):
        bybit_sym = f"{sym}"
        okx_sym = f"{sym}"

        try:
            price_bybit = bybit_tickers[bybit_sym]
            price_okx = okx_tickers[okx_sym]
        except KeyError:
            continue

        spread_pct = abs(price_bybit - price_okx) / ((price_bybit + price_okx) / 2)

        if spread_pct > THRESHOLD:
            print(f"📈 {sym}: Bybit = {price_bybit:.2f}, OKX = {price_okx:.2f}, Δ = {spread_pct * 100:.2f}%")
    
    

def __initialize(args):
    compare_prices()
     
    # try:
    #     __fetch_symbols(MarketType.FUTURES)
    #     __ws_connection_reset(MarketType.FUTURES)
        
    #     executor = ThreadPoolExecutor(max_workers=1)
    #     executor.submit(lambda: run_until_complete(lambda: __fetch_candles(MarketType.FUTURES)))
    #     executor.shutdown(wait=True)
    # finally:
    #     print("Starting Flask application (REST API endpoints)...")
    #     app.run(debug=args.debug, port=5003)

def main():
    try:
        print("Starting application...")
        
        # Configure argument parser
        parser = argparse.ArgumentParser(description="Default argument parser")
        parser.add_argument('--debug', action='store_true', help='Is debug mode enabled')

        __initialize(parser.parse_args())

    except KeyboardInterrupt:
        print("[KeyboardInterrupt] caught in main. Exiting application...")
        
if __name__ == "__main__":
    main()