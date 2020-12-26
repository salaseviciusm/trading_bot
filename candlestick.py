class Colour:
    RED = 0
    GREEN = 1
    NONE = 2

def colour(ohlc_candle):
    if ohlc_candle['open'] < ohlc_candle['close']:
        return Colour.GREEN
    elif ohlc_candle['open'] > ohlc_candle['close']:
        return Colour.RED
    else:
        return Colour.NONE

def isRed(ohlc_candle):
    return colour(ohlc_candle) == Colour.RED

def isGreen(ohlc_candle):
    return colour(ohlc_candle) == Colour.GREEN