class Signal:
    BUY = 0
    SELL = 1
    HOLD = 2

def SMA(data, periods=20):
    return data.rolling(periods).mean().iloc[-1]

def EMA(data, periods=20):
    return data.ewm(span=periods).mean().iloc[-1]

def has_crossed_value(ohlc_candle, target_value):
    return (ohlc_candle['open'] >= target_value and ohlc_candle['close'] <= target_value) \
        or (ohlc_candle['open'] <= target_value and ohlc_candle['close'] >= target_value)

def sma_signal(ohlc):
    """ Returns a Signal for the last candlestick in the ohlc data frame.
        * ohlc must have at least 2 elements
    """
    prev_candle = ohlc.iloc[-2]
    curr_candle = ohlc.iloc[-1]
    if has_crossed_value(prev_candle, SMA(ohlc.iloc[:-1]['close'])):
        if curr_candle['close'] > SMA(ohlc['close']):
            return Signal.BUY
        if curr_candle['close'] < SMA(ohlc['close']):
            return Signal.SELL
        return Signal.HOLD