import krakenex
from pykrakenapi import KrakenAPI

from trading_bot import Dispatcher, TradingBot
from chart_utils import display_graph, chart_signals, h_line
import mplfinance as mpf
import numpy as np
import pandas as pd
import time

from indicators import *

class TestDispatcher(Dispatcher):
    def __init__(self, balance=0, interval=5, pairs=[]):
        self.interval = interval
        self.data = {}
        self.last = None

        self.pairs = pairs
        self.ticker_info = None

        self.balance = balance
        self.positions = {}
        self.pnl = 0

        self.buys = {}
        self.sells = {}
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

            order = {'amount': amount, 'price': ask, 'stoploss': ask*0.99, 'takeprofit': ask*1.02}
            if pair in self.positions:
                self.positions[pair].append(order)
            else:
                self.positions[pair] = [order]
            self.buys[pair][-1] = ask

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
            self.sells[pair][-1] = bid
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
        return float(self.ticker_info.loc[pair]['a'][0])

    def current_bid_price(self, pair):
        return float(self.ticker_info.loc[pair]['b'][0])

    def get_ohlc_data(self, pair):
        if pair not in self.data:
            # OHLC is sorted so that the latest element is at OHLC.iloc[-1]
            ohlc, last = self.kraken.get_ohlc_data(pair, interval=self.interval, ascending=True)
            self.data[pair] = ohlc
            self.last = last
            self.buys[pair] = [np.nan for i in range(len(ohlc.index))]
            self.buys[pair][0] = ohlc.iloc[0]['open']
            self.sells[pair] = self.buys[pair].copy()
        else:
            ohlc, last = self.kraken.get_ohlc_data(pair, interval=self.interval, ascending=True, since=self.last)
            if len(ohlc.index) > 1:
                self.data[pair].iloc[-1] = ohlc.iloc[0]
                self.data[pair] = self.data[pair].append(ohlc.iloc[1:])
                self.last = last
            else:
                self.data[pair].iloc[-1] = ohlc.iloc[0]
            
            extension = [np.nan for i in range(len(ohlc.index)-1)]
            self.buys[pair].extend(extension)
            self.sells[pair].extend(extension)

        #if len(self.data[pair].index) > 800:
        #    self.data[pair] = self.data[pair].iloc[-750:]
            
        return self.data[pair]
    
    def update(self):
        time.sleep(5)
        
        self.ticker_info = self.kraken.get_ticker_information(','.join(self.pairs))
        for pair in self.pairs:
            if pair in self.positions:
                positions = self.positions[pair]
                bid = self.current_bid_price(pair)
                for position in positions:
                    if position['stoploss'] >= bid:
                        print("Stoploss activated for %s" % (str(position)))
                        self.sell(pair, bid, position)
                    elif position['takeprofit'] <= bid:
                        print("Takeprofit activated for %s" % (str(position)))
                        self.sell(pair, bid, position)

def TestTradingBot():
    pairs = ['ADAEUR']
    test_dispatcher = TestDispatcher(balance=1000, interval=1, pairs=pairs)
    test_bot = TradingBot(test_dispatcher, pairs=pairs)

    return test_bot

if __name__ == "__main__":
    test_bot = TestTradingBot()
    try:
        test_bot.strategy_2()
    except KeyboardInterrupt:
        print("Done")

        print('%d Trades made. %d Winners. %f%% Winners. %f%% %s'
            % (test_bot.dispatcher.trades,
               test_bot.dispatcher.winning_trades,
               100*test_bot.dispatcher.winning_trades/test_bot.dispatcher.trades if test_bot.dispatcher.trades > 0 else 0,
               100*(test_bot.dispatcher.pnl/1000),
               "up" if test_bot.dispatcher.pnl > 0 else "down"))

        for pair in test_bot.pairs:
            ohlc = test_bot.dispatcher.data[pair]
            print(len(ohlc.index))
            print(len(test_bot.dispatcher.buys[pair]))
            print(len(test_bot.dispatcher.sells[pair]))
            
            stoch_buy, stoch_sell, stoch_line = chart_signals(ohlc, stochastic_oscillator_signal, stochastic_oscillator)
            rsi_buy, rsi_sell, rsi_line = chart_signals(ohlc, RSI_signal, RSI, value_f_args={'period':14})
            #buy_ema, sell_ema, line_ema = chart_signals(ohlc, ema_crosses_higher_lower_sma_signal, SMA)
            display_graph(ohlc, add_plots=
            [
                {'data': test_bot.dispatcher.buys[pair], 'type':'scatter', 'markersize':100, 'marker':'*', 'color':'g', 'secondary_y':False},
                {'data': test_bot.dispatcher.sells[pair], 'type':'scatter', 'markersize':100, 'marker':'*', 'color':'r', 'secondary_y':False},
                {'data': ohlc['high'].rolling(30).mean(), 'color':'y'},
                {'data': ohlc['low'].rolling(30).mean(), 'color':'m'},
                {'data': ohlc['high'].ewm(span=30).mean(), 'color':'b'},
                {'data': ohlc['low'].ewm(span=30).mean(), 'color':'y'},
                {'data': ohlc['low'].ewm(span=100).mean(), 'color':'r'},
                {'data': stoch_buy, 'type':'scatter', 'markersize':100, 'marker':'*', 'color':'g', 'secondary_y':False, 'panel':1},
                {'data': stoch_sell, 'type':'scatter', 'markersize':100, 'marker':'*', 'color':'g', 'secondary_y':False, 'panel':1},
                {'data': stoch_line, 'panel':1, 'secondary_y':False},
                {'data': stoch_line.rolling(3).mean(), 'panel':1, 'secondary_y':False},
                {'data': h_line(80, len(ohlc.index)), 'panel':1, 'secondary_y':False, 'color':'black'},
                {'data': h_line(20, len(ohlc.index)), 'panel':1, 'secondary_y':False, 'color':'black'},
                {'data': rsi_line, 'panel':2, 'secondary_y':False},
                {'data': h_line(70, len(ohlc.index)), 'panel':2, 'secondary_y':False, 'color':'black'},
                {'data': h_line(30, len(ohlc.index)), 'panel':2, 'secondary_y':False, 'color':'black'},
            ])
