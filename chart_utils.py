from indicators import Signal
import numpy as np
import pandas as pd
import mplfinance as mpf
import matplotlib
matplotlib.use('TkAgg')


def h_line(y, length):
    """ Returns a pandas Series of size length which represents a horizontal line on the axis at value y=y
    """
    return pd.Series([y for i in range(length)])


def chart_signals(ohlc, signal_f, value_f, signal_f_args={}, value_f_args={}):
    """ Returns 3 lists:
        * One representing a scatter where the bot sent each buy order
        * One for sell orders
          (Both based on signal_f() placed at value_f())
        * One pandas Series representing the line for the signal indicator
    """
    buy = [np.nan for i in range(len(ohlc.index))]
    buy[0] = 0  # Ensure that the entire list isn't NaN as this will prevent MPL from plotting it
    sell = buy.copy()
    value_line = buy.copy()

    for i in range(0, len(ohlc.index)):
        signal = signal_f(ohlc.iloc[:i+1], **signal_f_args)
        value = value_f(ohlc.iloc[:i+1], **value_f_args)

        value_line[i] = value

        if signal == Signal.BUY:
            buy[i] = value
        elif signal == Signal.SELL:
            sell[i] = value

    return buy, sell, pd.Series(value_line)


def display_graph(ohlc, view_range=(1,), add_plots=[]):
    a = view_range[0]
    b = view_range[1] if len(view_range) > 1 else len(ohlc.index)

    added_plots = []
    for plot in add_plots:
        data = plot['data']
        del plot['data']

        added_plots.append(mpf.make_addplot(data[a:b], **plot))

    mpf.plot(ohlc.iloc[a:b], type='candlestick', addplot=added_plots)
    mpf.show()
