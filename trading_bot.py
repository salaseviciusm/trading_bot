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

    def strategy_1 (self, signal_func):
        while(True):
            ohlc = self.dispatcher.get_ohlc_data(self.kraken)
            
            curr_candle = ohlc.iloc[-1]

            signal = signal_func(ohlc[:-1])

            curr_ask = self.dispatcher.current_ask_price("ADAEUR")
            curr_bid = self.dispatcher.current_bid_price("ADAEUR")

            if signal == Signal.BUY:
                if isGreen(curr_candle):
                    self.dispatcher.buy("ADAEUR", int(self.dispatcher.balance / curr_ask), curr_ask)
            elif signal == Signal.SELL:
                if isRed(curr_candle):
                    self.dispatcher.sell("ADAEUR", curr_bid)
    
    def strategy_2 (self):
        while(True):
            ohlc = self.dispatcher.get_ohlc_data(self.kraken)
            
            curr_candle = ohlc.iloc[-1]

            signal = ema_crosses_higher_lower_sma_signal(ohlc[:-1])
            stoch_signal = stochastic_oscillator_signal(ohlc[:-1], 14, 3)

            curr_ask = self.dispatcher.current_ask_price("ADAEUR")
            curr_bid = self.dispatcher.current_bid_price("ADAEUR")

            if signal == Signal.BUY and stoch_signal != Signal.SELL:
                self.dispatcher.buy("ADAEUR", int(self.dispatcher.balance / curr_ask), curr_ask)
            elif signal == Signal.SELL and stoch_signal != Signal.BUY:
                self.dispatcher.sell("ADAEUR", curr_bid)


if __name__ == "__main__":
    api = krakenex.API()
    api.load_key('kraken.key')
    
    kraken = KrakenAPI(api)

    ohlc, _ = kraken.get_ohlc_data("ADAEUR", interval=5, ascending=True)

    buy, sell = chart_signals(ohlc, stochastic_oscillator_signal, stochastic_oscillator)

    import matplotlib
    import mplfinance as mpf
    import pandas as pd
    
    stochastic_line = []
    for i in range(1,ohlc['open'].size+1):
        stochastic_line.append(stochastic_oscillator(ohlc.iloc[:i], 14))
    stochastic_line = pd.Series(stochastic_line)

    r = 400
    display_graph(ohlc, r,
        mpf.make_addplot(buy[-r:], type='scatter', markersize=100, marker='*', color='g', panel=1, secondary_y=False),
        mpf.make_addplot(sell[-r:], type='scatter', markersize=100, marker='*', color='r', panel=1, secondary_y=False),
        mpf.make_addplot(stochastic_line[-r:], panel=1, secondary_y=False),
        mpf.make_addplot(stochastic_line.rolling(3).mean()[-r:], panel=1, secondary_y=False, marker='-'),
        mpf.make_addplot(pd.Series(80, index=range(r)), panel=1, secondary_y=False, color='black'),
        mpf.make_addplot(pd.Series(20, index=range(r)), panel=1, secondary_y=False, color='black'))