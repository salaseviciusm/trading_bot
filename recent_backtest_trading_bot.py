import krakenex
from pykrakenapi import KrakenAPI

from trading_bot import Dispatcher, TradingBot
import numpy as np
import time

from indicators import *


class TestDispatcher(Dispatcher):
    def __init__(self, balance=0, positions=dict(), pnl=0, interval=5):
        self.balance = balance
        self.positions = positions
        self.pnl = pnl
        self.data = {}
        self.tick = 0
        self.buys = {}
        self.sells = {}
        self.winning_trades = 0
        self.trades = 0
        self.interval = interval

        self.api = krakenex.API()
        self.api.load_key('kraken.key')

        self.kraken = KrakenAPI(self.api)

    def print_status(self):
        print("Balance: %f\nPositions: %s\nPnL: %f" % (self.balance, str(self.positions), self.pnl))

    def buy(self, pair):
        ask = self.current_ask_price(pair)
        bid = self.current_bid_price(pair)

        amount = self.balance / ask

        if amount <= 0:
            return
        if self.balance >= amount * ask:
            print("Buying %f %s at price %f" % (amount, pair, ask))
            self.balance -= amount * ask

            vol = volatility(self.data[pair].iloc[:self.tick])
            print("VOLATILITY %f" % vol)
            order = {'amount': amount, 'price': ask, 'stoploss': bid*(0.99-vol*0.02), 'takeprofit': ask*(1.005+vol*0.08) }
            if pair in self.positions:
                self.positions[pair].append(order)
            else:
                self.positions[pair] = [order]
            self.buys[pair][-1] = ask
            self.print_status()
            print("")
        else:
            print("Balance too low to buy %f %s at price %f" % (amount, pair, ask))

    # Sells the given pair
    def sell(self, pair):
        #ticker_info = self.kraken.get_ticker_information(pair)
        #bid = ticker_info['b'][pair][0]
        bid = self.current_bid_price(pair)

        while pair in self.positions and len(self.positions[pair]) > 0:
            position = self.positions[pair][0]

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

    def current_ask_price(self, pair):
        index = min(self.tick-1, len(self.data[pair].index) - 1)
        return self.data[pair].iloc[index]['open']

    def current_bid_price(self, pair):
        index = min(self.tick-1, len(self.data[pair].index) - 1)
        return self.data[pair].iloc[index]['open']

    def get_ohlc_data(self, pair):
        if pair not in self.data:
            # OHLC is sorted so that the latest element is at OHLC.iloc[-1]
            # ohlc, _ = self.kraken.get_ohlc_data("ADAEUR", interval=5, ascending=True)
            ohlc, _ = self.kraken.get_ohlc_data(pair, interval=self.interval, ascending=True)
            self.data[pair] = ohlc
            self.buys[pair] = []
            self.sells[pair] = []

        return self.data[pair].iloc[:self.tick]

    def update(self):
        self.tick += 1

        finished = True
        for pair in self.data:
            self.buys[pair].append(np.nan)
            self.sells[pair].append(np.nan)

            if pair in self.positions:
                positions = self.positions[pair]
                bid = self.current_bid_price(pair)
                ask = self.current_ask_price(pair)
                for position in positions:
                    if position['stoploss'] >= bid:
                        print("Stoploss activated for %s" % (str(position)))
                        self.sell(pair)
                    elif position['takeprofit'] <= bid:
                        print("Takeprofit activated for %s" % (str(position)))
                        self.sell(pair)

            if self.tick <= len(self.data[pair].index):
                finished = False

        if finished and len(self.data) > 0:
            print("----- Test complete -----")
            print('%d Trades made. %d Winners. %f%% Winners. %f%% %s'
                  % (self.trades,
                     self.winning_trades,
                     100*self.winning_trades/self.trades,
                     100*(self.pnl/1000),
                     "up" if self.pnl > 0 else "down"))
            time.sleep(10)


def TestTradingBot():
    test_dispatcher = TestDispatcher(balance=1000)
    test_bot = TradingBot(test_dispatcher, pairs=['ADAEUR'])

    return test_bot


if __name__ == "__main__":
    test_bot = TestTradingBot()
    try:
        test_bot.strategy_2(sleep=False)
    except KeyboardInterrupt:
        print("Done")

        from chart_utils import display_graph, chart_signals, h_line

        for pair in test_bot.pairs:
            ohlc = test_bot.dispatcher.data[pair]
            print(len(ohlc.index))
            print(len(test_bot.dispatcher.buys[pair]))
            print(len(test_bot.dispatcher.sells[pair]))

            stoch_buy, stoch_sell, stoch_line = chart_signals(ohlc, stochastic_oscillator_signal, stochastic_oscillator)
            rsi_buy, rsi_sell, rsi_line = chart_signals(ohlc, RSI_signal, RSI, value_f_args={'period':14})
            # buy_ema, sell_ema, line_ema = chart_signals(ohlc, ema_crosses_higher_lower_sma_signal, SMA)
            display_graph(ohlc, add_plots=
            [
                {'data': test_bot.dispatcher.buys[pair], 'type':'scatter', 'markersize':100, 'marker':'*', 'color':'g', 'secondary_y':False},
                {'data': test_bot.dispatcher.sells[pair], 'type':'scatter', 'markersize':50, 'marker':'*', 'color':'r', 'secondary_y':False},
                {'data': ohlc['high'].rolling(30).mean(), 'color':'y'},
                {'data': ohlc['low'].rolling(30).mean(), 'color':'m'},
                {'data': ohlc['high'].ewm(span=14).mean(), 'color':'b'},
                {'data': ohlc['low'].ewm(span=14).mean(), 'color':'C0'},
                {'data': ohlc['low'].ewm(span=100).mean(), 'color':'r'},
                {'data': stoch_buy, 'type':'scatter', 'markersize':100, 'marker':'*', 'color':'g', 'secondary_y':False, 'panel':1},
                {'data': stoch_sell, 'type':'scatter', 'markersize':100, 'marker':'*', 'color':'r', 'secondary_y':False, 'panel':1},
                {'data': stoch_line, 'panel':1, 'secondary_y':False},
                {'data': stoch_line.rolling(3).mean(), 'panel':1, 'secondary_y':False},
                {'data': h_line(80, len(ohlc.index)), 'panel':1, 'secondary_y':False, 'color':'black'},
                {'data': h_line(20, len(ohlc.index)), 'panel':1, 'secondary_y':False, 'color':'black'},
                {'data': rsi_line, 'panel':2, 'secondary_y':False},
                {'data': h_line(70, len(ohlc.index)), 'panel':2, 'secondary_y':False, 'color':'black'},
                {'data': h_line(30, len(ohlc.index)), 'panel':2, 'secondary_y':False, 'color':'black'},
            ])
