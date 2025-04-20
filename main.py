import ccxt
import pandas as pd
import json
import datetime
import asyncio
import requests
from config import t_token, t_chatid



class SymbolCycle:
    def __init__(self, filename):
        self.filename = filename
        self.symbols = self.load_symbols()
        self.current_index = 0

    def load_symbols(self):
        try:
            with open(self.filename, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return []

    def save_symbols(self):
        with open(self.filename, 'w') as file:
            json.dump(self.symbols, file)

    def get_next_symbol(self):
        if not self.symbols:
            return None

        ip_symbol = self.symbols[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.symbols)
        self.save_symbols()
        return ip_symbol


def telegrammessage(message):
    try:
        TOKEN = t_token
        CHAT_ID = t_chatid
        url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'

        params = {
            'chat_id': CHAT_ID,
            'text': message
        }

        requests.get(url, params=params)
    except Exception as e:
        print(f'Error: {e}')


async def price_percentage(symbol, timeframe):
    try:
        exchange = ccxt.bybit()  # Initialize the exchange object
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        df = pd.DataFrame(ohlcv, columns=columns)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        last_two_candles = df.iloc[-2:]
        close_prices = last_two_candles['close']
        price_change_percentage = ((close_prices.iloc[-1] - close_prices.iloc[-2]) / close_prices.iloc[-2]) * 100
        print(f"{datetime.datetime.now()} // {symbol}: {price_change_percentage:.2f}% {timeframe}         {close_prices.iloc[-1]} ")
        if abs(float(price_change_percentage)) > 2:
            print("+" * 55)
            print(f'Symbol {symbol}: {price_change_percentage}')
            message = f'Symbol {symbol}: {price_change_percentage}'
            telegrammessage(message)
        else:
            pass
    except Exception as e:
        print(f'Error: {symbol}, {e}')



async def cicle():
    symbol_cycle = SymbolCycle('symbols.json')
    timeframe = '5m'
    while True:
        symbol = symbol_cycle.get_next_symbol()
        if symbol is not None:
            await price_percentage(symbol, timeframe)
        if symbol == "ZRX/USDT:USDT":
            await asyncio.sleep(600)
        else:
            await asyncio.sleep(0.05)


async def main():
    while True:
        await cicle()
        await asyncio.sleep(60)  # Повторять каждый час


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
