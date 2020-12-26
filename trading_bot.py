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

class Signal:
    BUY = 0
    SELL = 1
    HOLD = 2

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

def chart_signals(ohlc, signal_func, value_func):
    """ Returns a series for the ohlc data that shows where the buy and sell signals are for
        the given signal_func(ohlc). These signals will be placed at the value given by
        value_func(ohlc).
    """
    buy = [np.nan]
    sell = [np.nan]

    for i in range(1, ohlc['open'].size):
        signal = signal_func(ohlc[:i+1])
        if signal == Signal.BUY:
            buy.append(value_func(ohlc[:i+1]))
            sell.append(np.nan)
        elif signal == Signal.SELL:
            buy.append(np.nan)
            sell.append(value_func(ohlc[:i+1]))
        else:
            buy.append(np.nan)
            sell.append(np.nan)

    return buy, sell

def sma_signal(ohlc):
    """ Returns a Signal for the last candlestick in the ohlc data frame.
        * ohlc must have at least 2 elements
    """
    prev_candle = ohlc.iloc[-2]
    curr_candle = ohlc.iloc[-1]
    if has_crossed_value(prev_candle, SMA(ohlc.iloc[:-1])):
        if curr_candle['open'] > SMA(ohlc):
            return Signal.BUY
        if curr_candle['open'] < SMA(ohlc):
            return Signal.SELL
        return Signal.HOLD


def display_graph(ohlc, r):
    buy, sell = chart_signals(ohlc, sma_signal, SMA)
    
    added_plots = [
        mpf.make_addplot(ohlc['close'].rolling(20).mean()[-r:]), # SMA line
        mpf.make_addplot(buy[-r:], type='scatter', markersize=50, marker='^'), # SMA Buy Signals
        mpf.make_addplot(sell[-r:], type='scatter', markersize=50, marker='v') # SMA Sell Signals
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

if __name__ == "__main__":
    api = krakenex.API()
    api.load_key('kraken.key')
    
    kraken = KrakenAPI(api)

    ohlc, _ = kraken.get_ohlc_data("ADAEUR", interval=5, ascending=True)

    display_graph(ohlc, 400)