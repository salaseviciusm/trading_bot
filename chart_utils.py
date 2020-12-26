import matplotlib
matplotlib.use('TkAgg')
import mplfinance as mpf

import numpy as np

from indicators import Signal, SMA, EMA, sma_signal

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
            buy.append(value_func(ohlc[:i+1]['close']))
            sell.append(np.nan)
        elif signal == Signal.SELL:
            buy.append(np.nan)
            sell.append(value_func(ohlc[:i+1]['close']))
        else:
            buy.append(np.nan)
            sell.append(np.nan)

    return buy, sell


def display_graph(ohlc, r, *addplots):
    buy, sell = chart_signals(ohlc, sma_signal, SMA)

    added_plots = [
        mpf.make_addplot(ohlc['close'].rolling(20).mean()[-r:]), # SMA line
        mpf.make_addplot(buy[-r:], type='scatter', markersize=50, marker='^'), # SMA Buy Signals
        mpf.make_addplot(sell[-r:], type='scatter', markersize=50, marker='v') # SMA Sell Signals
    ]

    if addplots is not None:
        added_plots.extend(addplots)

    mpf.plot(ohlc.iloc[-r:], type='candlestick', addplot=added_plots)
    mpf.show()