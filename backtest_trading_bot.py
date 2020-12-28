import krakenex
from pykrakenapi import KrakenAPI

from trading_bot import Dispatcher, TradingBot
from chart_utils import display_graph, chart_signals
import mplfinance as mpf
import numpy as np
import pandas as pd
import time

from indicators import *

class TestDispatcher(Dispatcher):
    def __init__(self, balance=0, positions=dict(), pnl=0):
        self.balance = balance
        self.positions = positions
        self.pnl = pnl
        self.data = {}
        self.tick = 0
        self.buys = []
        self.sells = []
        self.winning_trades = 0
        self.trades = 0

        self.api = krakenex.API()
        self.api.load_key('kraken.key')

        self.kraken = KrakenAPI(self.api)

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
            
            order = {'amount': amount, 'price': ask, 'stoploss': ask*0.99}
            if pair in self.positions:
                self.positions[pair].append(order)
            else:
                self.positions[pair] = [order]
            self.buys[-1] = ask

            self.print_status()
            print("")
        else:
            print("Balance too low to buy %f %s at price %f" % (amount, pair, ask))
    
    # Sells the given position. If no position given, sells all positions.
    def sell(self, pair, price, position=None):
        #ticker_info = self.kraken.get_ticker_information(pair)
        #bid = ticker_info['b'][pair][0]
        bid = price

        if pair in self.positions and position in self.positions[pair]:
            print("Selling %f %s at price %f" % (position['amount'], pair, bid))
            self.balance += position['amount'] * bid

            profit = position['amount'] * (bid - position['price'])
            if profit > 0:
                self.winning_trades += 1

            self.pnl += profit
            self.positions[pair].remove(position)
            if len(self.positions[pair]) == 0:
                del self.positions[pair]
            self.sells[-1] = bid
            self.trades += 1

            self.print_status()
            print("")
        else:
            if position is None:
                while pair in self.positions and len(self.positions[pair]) > 0:
                    self.sell(pair, price, self.positions[pair][0])
            else:
                print("This position does not exist.")
    
    def current_ask_price(self, pair):
        index = min(self.tick-1, len(self.data[pair]) - 1)
        return self.data[pair].iloc[index]['open']

    def current_bid_price(self, pair):
        index = min(self.tick-1, len(self.data[pair]) - 1)
        return self.data[pair].iloc[index]['open']

    def get_ohlc_data(self, pair):
        if pair not in self.data:
            # OHLC is sorted so that the latest element is at OHLC.iloc[-1]
            #ohlc, _ = self.kraken.get_ohlc_data("ADAEUR", interval=5, ascending=True)
            ohlc = pd.read_csv('backtest_data/%s_5.csv' % (pair), names=['time', 'open', 'high', 'low', 'close', 'volume', 'count'])
            ohlc['dtime'] = pd.to_datetime(ohlc.time, unit='s')
            ohlc.sort_values('dtime', ascending=True, inplace=True)
            ohlc.set_index('dtime', inplace=True)
            self.data[pair] = ohlc
        
        if self.tick >= len(self.data[pair].index):
            print("----- Test complete -----")
            print('%d Trades made. %d Winners. %f%% Winners. %f%% %s'
            % (test_bot.dispatcher.trades,
               test_bot.dispatcher.winning_trades,
               100*test_bot.dispatcher.winning_trades/test_bot.dispatcher.trades,
               100*(test_bot.dispatcher.pnl/1000),
               "up" if test_bot.dispatcher.pnl > 0 else "down"))
            time.sleep(10)
            
        return self.data[pair].iloc[:self.tick]
    
    def update(self):
        self.tick += 1

        self.buys.append(np.nan)
        self.sells.append(np.nan)
        
        for pair in self.data:
            if pair in self.positions:
                positions = self.positions[pair]
                bid = self.current_bid_price(pair)
                for position in positions:
                    if position['stoploss'] >= bid:
                        print("Stoploss activated for %s" % (str(position)))
                        self.sell(pair, bid, position)

def TestTradingBot():
    test_dispatcher = TestDispatcher(balance=1000)
    test_bot = TradingBot(test_dispatcher, pairs=['BCHGBP'])

    return test_bot

if __name__ == "__main__":
    test_bot = TestTradingBot()
    try:
        test_bot.strategy_2()
    except KeyboardInterrupt:
        print("Done")

        buy1, sell1 = chart_signals(test_bot.dispatcher.data, stochastic_oscillator_signal, stochastic_oscillator)
        ohlc = test_bot.dispatcher.data

        r = len(ohlc.index)

        stochastic_line = []
        for i in range(1,ohlc['open'].size+1):
            stochastic_line.append(stochastic_oscillator(ohlc.iloc[:i], 14))
        stochastic_line = pd.Series(stochastic_line)

        rsi_line = []
        for i in range(1, ohlc['open'].size+1):
            rsi_line.append(RSI(ohlc.iloc[:i], 14))
        rsi_line = pd.Series(rsi_line)

        buy, sell = chart_signals(test_bot.dispatcher.data, ema_crosses_higher_lower_sma_signal, SMA)
        ohlc = test_bot.dispatcher.data
        display_graph(test_bot.dispatcher.data, r,
            mpf.make_addplot(test_bot.dispatcher.buys[-r:], type='scatter', markersize=100, marker='*', color='g'),
            mpf.make_addplot(test_bot.dispatcher.sells[-r:], type='scatter', markersize=100, marker='*', color='r'),
            #mpf.make_addplot(buy[-r:], type='scatter', markersize=100, marker='^'),
            #mpf.make_addplot(sell[-r:], type='scatter', markersize=100, marker='v'),
            mpf.make_addplot(ohlc['high'].rolling(30).mean()[-r:], color='y'),
            mpf.make_addplot(ohlc['low'].rolling(30).mean()[-r:], color='m'),
            mpf.make_addplot(ohlc['low'].ewm(span=100).mean()[-r:], color='r'),
            mpf.make_addplot(ohlc['low'].ewm(span=14).mean()[-r:], color='b'),
            mpf.make_addplot(ohlc['high'].ewm(span=14).mean()[-r:], color='g'),
            mpf.make_addplot(buy1[-r:], type='scatter', markersize=100, marker='*', color='g', secondary_y=False, panel=1),
            mpf.make_addplot(sell1[-r:], type='scatter', markersize=100, marker='*', color='r', secondary_y=False, panel=1),
            mpf.make_addplot(stochastic_line[-r:], panel=1, secondary_y=False),
            mpf.make_addplot(stochastic_line.rolling(3).mean()[-r:], panel=1, secondary_y=False, marker='-'),
            mpf.make_addplot(pd.Series(80, index=range(r)), panel=1, secondary_y=False, color='black'),
            mpf.make_addplot(pd.Series(20, index=range(r)), panel=1, secondary_y=False, color='black'),
            mpf.make_addplot(rsi_line.iloc[-r:], panel=2, secondary_y=False),
            mpf.make_addplot(pd.Series(70, index=range(r)), panel=2, secondary_y=False, color='black'),
            mpf.make_addplot(pd.Series(30, index=range(r)), panel=2, secondary_y=False, color='black')
            )