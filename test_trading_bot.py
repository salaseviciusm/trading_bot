from trading_bot import Dispatcher, TradingBot
from chart_utils import display_graph, chart_signals
import mplfinance as mpf
import numpy as np
import time

from indicators import *

class TestDispatcher(Dispatcher):
    def __init__(self, balance=0, positions=dict(), pnl=0):
        self.balance = balance
        self.positions = positions
        self.pnl = pnl
        self.data = None
        self.tick = 0
        self.buys = []
        self.sells = []

    def print_status(self):
        print("Balance: %f\nPositions: %s\nPnL: %f" % (self.balance, str(self.positions), self.pnl))

    def buy(self, pair, amount, price):
        #ticker_info = self.kraken.get_ticker_information(pair)
        #ask = ticker_info['a'][pair][0]
        ask = price

        if amount <= 0:
            return
        if self.balance >= amount * ask:
            print("Buying %f %s at price %f" % (amount, pair, ask))
            self.balance -= amount * ask
            self.positions[pair].append({'amount': amount, 'price': ask})
            self.buys[-1] = ask
        else:
            print("Balance too low to buy %f %s at price %f" % (amount, pair, ask))
        self.print_status()
        print("")
    
    # Sells the given position. If no position given, sells all positions.
    def sell(self, pair, price, position=None):
        #ticker_info = self.kraken.get_ticker_information(pair)
        #bid = ticker_info['b'][pair][0]
        bid = price

        if position in self.positions[pair]:
            print("Selling %f %s at price %f" % (position['amount'], pair, bid))
            self.balance += position['amount'] * bid
            self.pnl += position['amount'] * (bid - position['price'])
            self.positions[pair].remove(position)
            self.sells[-1] = bid
        else:
            if position is None:
                while len(self.positions[pair]) > 0:
                    self.sell(pair, price, self.positions[pair][0])
                print("No positions left to sell.")
            else:
                print("This position does not exist.")
        self.print_status()
        print("")
    
    def current_ask_price(self, pair):
        index = min(self.tick-1, self.data['open'].size - 1)
        return self.data.iloc[index]['open']

    def current_bid_price(self, pair):
        index = min(self.tick-1, self.data['open'].size - 1)
        return self.data.iloc[index]['open']

    def get_ohlc_data(self, kraken):
        if self.tick == 0:
            # OHLC is sorted so that the latest element is at OHLC.iloc[-1]
            ohlc, _ = kraken.get_ohlc_data("ADAEUR", interval=5, ascending=True)
            self.data = ohlc
            self.tick = 2
        
        if self.tick >= self.data['open'].size:
            print("----- Test complete -----")
            time.sleep(10)

        self.tick += 1

        self.buys.append(np.nan)
        self.sells.append(np.nan)
            
        return self.data.iloc[:self.tick]

def TestTradingBot():
    test_dispatcher = TestDispatcher(balance=1000, positions={"ADAEUR": []})
    test_bot = TradingBot(test_dispatcher)

    return test_bot

if __name__ == "__main__":
    test_bot = TestTradingBot()
    try:
        test_bot.strategy_1(ema_crosses_higher_lower_sma_signal)
    except KeyboardInterrupt:
        print("Done")
        buy, sell = chart_signals(test_bot.dispatcher.data, ema_crosses_higher_lower_sma_signal, SMA)
        ohlc = test_bot.dispatcher.data
        display_graph(test_bot.dispatcher.data, 200,
            mpf.make_addplot(test_bot.dispatcher.buys[-200:], type='scatter', markersize=100, marker='*', color='g'),
            mpf.make_addplot(test_bot.dispatcher.sells[-200:], type='scatter', markersize=100, marker='*', color='r'),
            mpf.make_addplot(buy[-200:], type='scatter', markersize=100, marker='^'),
            mpf.make_addplot(sell[-200:], type='scatter', markersize=100, marker='v'),
            mpf.make_addplot(ohlc['high'].rolling(40).mean()[-200:]),
            mpf.make_addplot(ohlc['low'].rolling(40).mean()[-200:]),
            mpf.make_addplot(ohlc['low'].ewm(span=15).mean()[-200:]))