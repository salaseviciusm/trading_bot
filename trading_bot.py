import krakenex
from pykrakenapi import KrakenAPI

import numpy as np

from abc import ABC

import time

from candlestick import isRed, isGreen
from chart_utils import chart_signals, display_graph, h_line
from indicators import *


class DispatcherData():
    """
    A class that stores the Dispatcher's data, such as OHLC data and the buys/sells array for each pair
    """
    def __init__(self):
        pass

class Dispatcher(ABC):
    """
    Abstract class that the bot will use for retrieving price data and buy/sell orders
    in the way that child classes decide to implement this class.
    Deriving classes could, for example, be used to create dispatchers for different
    exchanges, as well as for testing strategies.
    """

    def buy(self, pair, amount, price):
        raise NotImplementedError

    def sell(self, pair, price, position):
        raise NotImplementedError

    def current_ask_price(self, pair):
        raise NotImplementedError

    def current_bid_price(self, pair):
        raise NotImplementedError

    def get_ohlc_data(self, pair):
        raise NotImplementedError
    
    # Used to update the state of the dispatcher once each cycle
    def update(self):
        raise NotImplementedError

class TradingBot:
    def __init__(self, dispatcher, pairs=[]):
        self.dispatcher = dispatcher
        self.pairs = pairs

    def strategy_1 (self, signal_func, signal_func_args={}):
        while(True):
            self.dispatcher.update()

            for pair in self.pairs:
                ohlc = self.dispatcher.get_ohlc_data(pair)
                
                curr_candle = ohlc.iloc[-1]

                signal = signal_func(ohlc[:-1], **signal_func_args)

                if signal == Signal.BUY:
                    if isGreen(curr_candle):
                        curr_ask = self.dispatcher.current_ask_price(pair)
                        self.dispatcher.buy(pair, int(self.dispatcher.balance / curr_ask), curr_ask)
                elif signal == Signal.SELL:
                    if isRed(curr_candle):
                        curr_bid = self.dispatcher.current_bid_price(pair)
                        self.dispatcher.sell(pair, curr_bid)
    
    def strategy_2 (self):
        while(True):
            self.dispatcher.update()

            for pair in self.pairs:
                ohlc = self.dispatcher.get_ohlc_data(pair)
                
                curr_candle = ohlc.iloc[-1]

                signal = ema_crosses_higher_lower_sma_signal(ohlc[:-1])
                stoch_signal = stochastic_oscillator_signal(ohlc[:-1], kperiod=14, dperiod=3)
                rsi = RSI(ohlc[:-1], 14)

                if signal == Signal.BUY and stoch_signal != Signal.SELL and (EMA(ohlc['low'], 14) > EMA(ohlc['low'],100) or rsi < 30):
                    #print("Buy!")
                    curr_ask = self.dispatcher.current_ask_price(pair)
                    self.dispatcher.buy(pair, int(self.dispatcher.balance / curr_ask), curr_ask)
                elif signal == Signal.SELL and stoch_signal != Signal.BUY:
                    #print("Sell!")
                    curr_bid = self.dispatcher.current_bid_price(pair)
                    self.dispatcher.sell(pair, curr_bid)


if __name__ == "__main__":
    api = krakenex.API()
    api.load_key('kraken.key')
    
    kraken = KrakenAPI(api)

    import matplotlib
    import mplfinance as mpf
    import pandas as pd

    ticker_info = kraken.get_ticker_information('ADAEUR,BCHGBP')
    print(ticker_info)
    input()
    ohlc, _ = kraken.get_ohlc_data("ADAEUR", interval=5, ascending=True)

    buy, sell, line = chart_signals(ohlc, stochastic_oscillator_signal, stochastic_oscillator)

    display_graph(ohlc, (400,),
    [
        {'data': buy, 'type':'scatter', 'markersize':100, 'marker':'*', 'color':'g', 'panel':1, 'secondary_y':False},
        {'data': sell, 'type':'scatter', 'markersize':100, 'marker':'*', 'color':'r', 'panel':1, 'secondary_y':False},
        {'data': line, 'color':'C1', 'panel':1, 'secondary_y':False},
        {'data': line.rolling(3).mean(), 'panel':1, 'secondary_y':False},
        {'data': h_line(80, len(ohlc.index)), 'panel':1, 'secondary_y':False, 'color':'black'},
        {'data': h_line(20, len(ohlc.index)), 'panel':1, 'secondary_y':False, 'color':'black'}
    ])