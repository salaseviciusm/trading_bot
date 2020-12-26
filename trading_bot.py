import krakenex
from pykrakenapi import KrakenAPI

import numpy as np

import matplotlib
matplotlib.use('TkAgg')
import mplfinance as mpf
import matplotlib.pyplot as plt

from abc import ABC

import time

class Colour:
    RED = 0
    GREEN = 1
    NONE = 2

def colour(ohlc_candle):
    if ohlc_candle['open'] < ohlc_candle['close']:
        return Colour.GREEN
    elif ohlc_candle['open'] > ohlc_candle['close']:
        return Colour.RED
    else:
        return Colour.NONE

def SMA(ohlc, periods=20):
    return ohlc['close'].rolling(periods).mean().iloc[-1]

def EMA(ohlc, periods=20):
    return ohlc['close'].ewm(span=periods).mean().iloc[-1]

def has_crossed_value(ohlc_candle, target_value):
    return (ohlc_candle['open'] >= target_value and ohlc_candle['close'] <= target_value) \
        or (ohlc_candle['open'] <= target_value and ohlc_candle['close'] >= target_value)

def sma_buy_signal(ohlc):
    signal = []
    i = 0
    for date, row in ohlc.iterrows():
        if i == 0:
            signal.append(np.nan)
            i += 1
            continue
        else:
            prev_candle = ohlc.iloc[i-1]
            curr_candle = ohlc.iloc[i]
            if has_crossed_value(prev_candle, SMA(ohlc[:i])):
                if curr_candle['open'] > SMA(ohlc[:i+1]):
                    signal.append(SMA(ohlc[:i+1]))
                    i += 1
                    continue
            signal.append(np.nan)
        i += 1

    return signal

def sma_sell_signal(ohlc):
    signal = []
    i = 0
    for date, row in ohlc.iterrows():
        if i == 0:
            signal.append(np.nan)
            i += 1
            continue
        else:
            prev_candle = ohlc.iloc[i-1]
            curr_candle = ohlc.iloc[i]
            if has_crossed_value(prev_candle, SMA(ohlc[:i])):
                if curr_candle['open'] < SMA(ohlc[:i+1]):
                    signal.append(SMA(ohlc[:i+1]))
                    i += 1
                    continue
            signal.append(np.nan)
        i += 1

    return signal

def display_graph(ohlc, r):
    added_plots = [mpf.make_addplot(ohlc['close'].rolling(20).mean()[-r:]), #SMA
        mpf.make_addplot(sma_buy_signal(ohlc)[-r:], type='scatter', markersize=50, marker='^'), #SMA Buy Signals
        mpf.make_addplot(sma_sell_signal(ohlc)[-r:], type='scatter', markersize=50, marker='v') #SMA Sell Signals
        ]

    mpf.plot(ohlc.iloc[-r:], type='candlestick', addplot=added_plots)
    mpf.show()

class Dispatcher(ABC):
    def buy(self, pair, amount, price):
        raise NotImplementedError

    def sell(self, pair, price, position):
        raise NotImplementedError

    def current_ask_price(self, pair):
        raise NotImplementedError

    def current_bid_price(self, pair):
        raise NotImplementedError

    def get_ohlc_data(self, kraken):
        raise NotImplementedError

class TestDispatcher(Dispatcher):
    def __init__(self, balance=0, positions=dict(), pnl=0):
        self.balance = balance
        self.positions = positions
        self.pnl = pnl
        self.data = None
        self.tick = 0

    def print_status(self):
        print("Balance: %f\nPositions: %s\nPnL: %f" % (self.balance, str(self.positions), self.pnl))

    def buy(self, pair, amount, price):
        #ticker_info = self.kraken.get_ticker_information(pair)
        #ask = ticker_info['a'][pair][0]
        ask = price

        if self.balance >= amount * ask:
            print("Buying %f %s at price %f" % (amount, pair, ask))
            self.balance -= amount * ask
            self.positions[pair].append({'amount': amount, 'price': ask})
        else:
            print("Balance too low to buy %f %s at price %f" % (amount, pair, ask))
        self.print_status()
        print("")
    
    # Sells the given position. If no position given, sells all positions.
    def sell(self, pair, price, position=None):
        #ticker_info = self.kraken.get_ticker_information(pair)
        #bid = ticker_info['b'][pair][0]
        bid = price

        if position in self.positions[pair]:
            print("Selling %f %s at price %f" % (position['amount'], pair, bid))
            self.balance += position['amount'] * bid
            self.pnl += position['amount'] * (bid - position['price'])
            self.positions[pair].remove(position)
        else:
            if position is None:
                while len(self.positions[pair]) > 0:
                    self.sell(pair, price, self.positions[pair][0])
                print("No positions left to sell.")
            else:
                print("This position does not exist.")
        self.print_status()
        print("")
    
    def current_ask_price(self, pair):
        index = min(self.tick + 1, self.data['open'].size - 1)
        return self.data.iloc[index]['open']

    def current_bid_price(self, pair):
        index = min(self.tick + 1, self.data['open'].size - 1)
        return self.data.iloc[index]['open']

    def get_ohlc_data(self, kraken):
        if self.tick == 0:
            # OHLC is sorted so that the latest element is at OHLC.iloc[-1]
            ohlc, _ = kraken.get_ohlc_data("ADAEUR", interval=5, ascending=True)
            self.data = ohlc
            self.tick = 3
            display_graph(ohlc, 100)
        
        if self.tick >= self.data['open'].size:
            print("----- Test complete -----")
            time.sleep(10)
        self.tick += 1
            
        return self.data.iloc[:self.tick-1]

    

class TradingBot:
    def __init__(self, dispatcher):
        self.api = krakenex.API()
        self.api.load_key('kraken.key')

        self.kraken = KrakenAPI(self.api)

        self.dispatcher = dispatcher

    def strategy_1 (self):
        while(True):
            ohlc = self.dispatcher.get_ohlc_data(self.kraken)
            
            prev_candle = ohlc.iloc[-2]
            curr_candle = ohlc.iloc[-1]

            # If previous candle crossed the SMA ...
            if has_crossed_value(prev_candle, SMA(ohlc.iloc[:-2])):
                curr_price = self.dispatcher.current_ask_price("ADAEUR")

                # If the current candle opens above the SMA
                if curr_candle['open'] > SMA(ohlc.iloc[:-1]):
                    print("Buy signal")
                    self.dispatcher.buy("ADAEUR", int(self.dispatcher.balance / curr_price), curr_price)
                
                # If the current candle opens below the SMA
                if curr_candle['open'] < SMA(ohlc.iloc[:-1]):
                    print("Sell signal")
                    self.dispatcher.sell("ADAEUR", curr_price)

def TestTradingBot():
    test_dispatcher = TestDispatcher(balance=1000, positions={"ADAEUR": []})
    test_bot = TradingBot(test_dispatcher)

    return test_bot

if __name__ == "__main__":
    test_bot = TestTradingBot()
    try:
        test_bot.strategy_1()
    except KeyboardInterrupt:
        print("Done")