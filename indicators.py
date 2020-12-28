from candlestick import isGreen, isRed
import pandas as pd
import numpy as np

class Signal:
    BUY = 0
    SELL = 1
    HOLD = 2

def SMA(data, periods=20):
    if len(data.index) == 0:
        return np.nan
    return data.rolling(periods).mean().iloc[-1]

def EMA(data, periods=20):
    if len(data.index) == 0:
        return np.nan
    return data.ewm(span=periods).mean().iloc[-1]

def has_crossed_value(ohlc_candle, target_value):
    return (ohlc_candle['open'] >= target_value and ohlc_candle['close'] <= target_value) \
        or (ohlc_candle['open'] <= target_value and ohlc_candle['close'] >= target_value)

def sma_signal(ohlc):
    """ Returns a Signal for the last candlestick in the ohlc data frame.
        * ohlc must have at least 2 elements
    """
    if len(ohlc.index) < 2:
        return Signal.HOLD

    prev_candle = ohlc.iloc[-2]
    curr_candle = ohlc.iloc[-1]
    if has_crossed_value(prev_candle, SMA(ohlc.iloc[:-1]['close'])):
        if curr_candle['close'] > SMA(ohlc['close']) and isGreen(prev_candle):
            return Signal.BUY
        if curr_candle['close'] < SMA(ohlc['close']) and isRed(prev_candle):
            return Signal.SELL
    return Signal.HOLD

def higher_lower_sma_signal(ohlc):
    """ Returns BUY if candle is completely above higher moving average,
        SELL if candle is completely below lower moving average,
        and HOLD in all other cases
    """
    if len(ohlc.index) < 2:
        return Signal.HOLD

    high_sma = SMA(ohlc['high'], 40)
    low_sma = SMA(ohlc['low'], 40)

    prev_candle = ohlc.iloc[-2]
    curr_candle = ohlc.iloc[-1]
    if curr_candle['low'] > high_sma and isGreen(prev_candle):
        return Signal.BUY
    if curr_candle['high'] < low_sma and isRed(prev_candle):
        return Signal.SELL
    return Signal.HOLD

def ema_crosses_higher_lower_sma_signal(ohlc):
    high_sma = SMA(ohlc['high'], 30)
    low_sma = SMA(ohlc['low'], 30)
    
    if EMA(ohlc['high'], 15) > low_sma:
        return Signal.BUY
    if EMA(ohlc['low'], 15) < high_sma:
        return Signal.SELL
    return Signal.HOLD

def stochastic_oscillator(ohlc, period=14):
    """
    Returns the value of K% for the latest candle in ohlc based on the given period
    """
    if len(ohlc.index) == 0:
        return np.nan

    p = min(ohlc['low'].size, period)

    # Lowest low in the period
    ll = ohlc[-p:].min()['low']
    
    # Highest high in the period
    hh = ohlc[-p:].max()['high']

    k = 100*(ohlc.iloc[-1]['close']-ll)/(hh-ll)

    return k

def close(ohlc):
    return ohlc.iloc[-1]['close'] if len(ohlc.index) > 0 else np.nan

def stochastic_oscillator_signal(ohlc, kperiod=14, dperiod=3):
    """
    Returns the signal returned by a stochastic oscillator indicator with kperiod on the calculation and
    dperiod SMA of the K value.
    Returns BUY when there are oversold conditions and the K line crosses above the D line
    """

    if len(ohlc.index) < max(kperiod, dperiod):
        return Signal.HOLD

    kvals = []
    for i in range (1, dperiod):
        kvals.append(stochastic_oscillator(ohlc[:-dperiod+i], kperiod))
    kvals.append(stochastic_oscillator(ohlc, kperiod))

    k = pd.Series(kvals)
    d = SMA(k, dperiod)

    if k.iloc[-1] < 20 and d < 20:
        if k.iloc[-1] > d :
            return Signal.BUY

    if k.iloc[-1] > 80 and d > 80:
        if k.iloc[-1] < d:
            return Signal.SELL

    return Signal.HOLD

def RSI(ohlc, period):
    # rsi = 100 - [100 / (1 + (avg price up / avg price down))]
    if len(ohlc.index) == 0:
        return np.nan

    deltas           =  ohlc['close'].diff()
    seed             =  deltas[-period:]
    up               =  seed[seed >= 0].sum() / period
    down             = -seed[seed <  0].sum() / period
    rs               =  up / down if down != 0 else 0

    # # Smoothing values
    # for i in range(period, ohlc['open'].size):
    #     delta = deltas[i]

    #     if  delta   >  0:
    #         upval   =  delta
    #         downval =  0.
    #     else:
    #         upval   =  0.
    #         downval = -delta

    #     up   = ( up   * ( period - 1 ) + upval   ) / period
    #     down = ( down * ( period - 1 ) + downval ) / period

    #     rs      = up / down

    #     rsi[i]  = 100. - ( 100. / ( 1. + rs ) )

    return 100 - (100 / (1 + rs))
    
def RSI_signal(ohlc, period=14):
    rsi = RSI(ohlc, period)
    if rsi > 70:
        return Signal.SELL
    elif rsi < 30:
        return Signal.BUY
    return Signal.HOLD
