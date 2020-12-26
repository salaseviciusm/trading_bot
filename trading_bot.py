import krakenex
from pykrakenapi import KrakenAPI

import numpy as np

from abc import ABC

import time

from candlestick import isRed, isGreen
from chart_utils import chart_signals, display_graph
from indicators import *

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
            
            curr_candle = ohlc.iloc[-1]
            crossing_candle = ohlc.iloc[-3] # Candle that crossed the SMA if signal is BUY or SELL

            signal = sma_signal(ohlc[:-1])

            curr_ask = self.dispatcher.current_ask_price("ADAEUR")
            curr_bid = self.dispatcher.current_bid_price("ADAEUR")

            self.dispatcher.buys.append(np.nan)
            self.dispatcher.sells.append(np.nan)
            if signal == Signal.BUY and isGreen(crossing_candle):
                if curr_ask >= curr_candle['open']:
                    print("Buy signal")
                    self.dispatcher.buy("ADAEUR", int(self.dispatcher.balance / curr_ask), curr_ask)
                    self.dispatcher.buys[-1] = curr_ask
            elif signal == Signal.SELL and isRed(crossing_candle):
                if curr_bid <= curr_candle['open']:
                    print("Sell signal")
                    self.dispatcher.sell("ADAEUR", curr_bid)
                    self.dispatcher.sells[-1] = curr_bid

if __name__ == "__main__":
    api = krakenex.API()
    api.load_key('kraken.key')
    
    kraken = KrakenAPI(api)

    ohlc, _ = kraken.get_ohlc_data("ADAEUR", interval=5, ascending=True)

    display_graph(ohlc, 400)