import matplotlib
matplotlib.use('TkAgg')
import mplfinance as mpf

import numpy as np

from indicators import Signal, SMA, EMA, sma_signal

def chart_signals(ohlc, signal_func, value_func, signal_func_args={}, value_func_args={}):
    """ Returns a series for the ohlc data that shows where the buy and sell signals are for
        the given signal_func(ohlc). These signals will be placed at the value given by
        value_func(ohlc).
    """
    buy = [np.nan for i in range (len(ohlc.index))]
    sell = buy.copy()

    for i in range(0, len(ohlc.index)):
        signal = signal_func(ohlc.iloc[:i+1], **signal_func_args)
        value = value_func(ohlc.iloc[:i+1], **value_func_args)

        if signal == Signal.BUY:
            buy[i] = value
        elif signal == Signal.SELL:
            sell[i]= value

    return buy, sell


def display_graph(ohlc, r, *addplots):
    added_plots = []
    if addplots is not None:
        added_plots = list(addplots)

    mpf.plot(ohlc.iloc[-r:], type='candlestick', addplot=added_plots)
    mpf.show()