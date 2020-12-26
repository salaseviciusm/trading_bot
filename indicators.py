from candlestick import isGreen, isRed

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
    high_sma = SMA(ohlc['high'], 40)
    low_sma = SMA(ohlc['low'], 40)

    prev_candle = ohlc.iloc[-2]
    if EMA(ohlc['low'], 15) > high_sma:
        return Signal.BUY
    if EMA(ohlc['low'], 15) < low_sma:
        return Signal.SELL
    return Signal.HOLD