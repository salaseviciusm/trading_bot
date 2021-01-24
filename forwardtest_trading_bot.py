import krakenex
from pykrakenapi import KrakenAPI

from trading_bot import Dispatcher, TradingBot
import numpy as np

from indicators import *

import threading


class TestDispatcher(Dispatcher):
    def __init__(self, balance=0, interval=5, pairs=[]):
        self.interval = interval
        self.data = {}
        self.last = None

        self.pairs = pairs
        self.ticker_info = {}

        self.balance = balance
        self.positions = {}
        self.pnl = 0

        self.buys = {}
        self.sells = {}
        self.winning_trades = 0
        self.trades = 0

        self.sell_lock = threading.Lock()

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

            vol = volatility(self.data[pair])
            print("VOLATILITY %f" % vol)
            order = {'amount': amount, 'price': ask, 'stoploss': bid*(1-vol*0.03), 'takeprofit': ask*(1+vol*0.07) }
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
    def sell(self, pair):
        bid = self.current_bid_price(pair)

        self.sell_lock.acquire()
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
        self.sell_lock.release()

    def current_ask_price(self, pair):
        return self.ticker_info[pair]['ask']

    def current_bid_price(self, pair):
        return self.ticker_info[pair]['bid']

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
            self.data[pair].iloc[-1] = ohlc.iloc[0]
            if len(ohlc.index) > 1:
                self.data[pair] = self.data[pair].append(ohlc.iloc[1:])
                self.last = last

            extension = [np.nan for i in range(len(ohlc.index)-1)]
            self.buys[pair].extend(extension)
            self.sells[pair].extend(extension)

        # if len(self.data[pair].index) > 800:
        #   self.data[pair] = self.data[pair].iloc[-750:]

        return self.data[pair]

    def update(self):
        pass

    # Called whenever new ticker information is delivered by the WebSocket API
    def update_ticker(self, pair, data):
        info = data[1]
        ask = float(info['a'][0])
        bid = float(info['b'][0])
        print("PAIR %s ASK: %s BID: %s" % (pair, ask, bid))

        self.ticker_info[pair] = {'ask': ask, 'bid': bid}

        positions = self.positions[pair]
        for position in positions:
            if position['stoploss'] >= bid:
                print("Stoploss activated for %s" % (str(position)))
                self.sell(pair)
            elif position['takeprofit'] <= bid:
                print("Takeprofit activated for %s" % (str(position)))
                self.sell(pair)


def TestTradingBot():
    pairs = ['ADAEUR']
    interval = 1

    test_dispatcher = TestDispatcher(balance=1000, interval=interval, pairs=pairs)
    test_bot = TradingBot(test_dispatcher, pairs=pairs)

    ws_names = test_dispatcher.kraken.get_tradable_asset_pairs(pair=','.join(pairs))['wsname']

    import websocket
    import _thread
    import json

    ws_channels = {}

    # Define WebSocket callback functions
    def ws_message(ws, message):
        j = json.loads(message)
        if 'channelID' in j:
            ws_channels[j['channelID']] = {'pair':j['pair'], 'subscription':j['subscription']}

        if '[' == message[0]:
            cID = j[0]
            pair = ws_names[ws_names == j[-1]].index[0]
            if ws_channels[cID]['subscription']['name'] == 'ticker':
                test_bot.dispatcher.update_ticker(pair, j)

    def ws_open(ws):
        for pair in ws_names.array:
            #ws.send('{"event":"subscribe", "subscription":{"name":"ohlc", "interval":%d}, "pair":["%s"]}' % (interval, pair))
            ws.send('{"event":"subscribe", "subscription":{"name":"ticker"}, "pair":["%s"]}' % (pair))

    def ws_thread(*args):
        ws = websocket.WebSocketApp("wss://ws.kraken.com/", on_open = ws_open, on_message = ws_message)
        ws.run_forever()

    # Start a new thread for the WebSocket interface
    _thread.start_new_thread(ws_thread, ())

    return test_bot


if __name__ == "__main__":
    test_bot = TestTradingBot()

    try:
        test_bot.strategy_2()
    except KeyboardInterrupt:
        print("Done")

        from chart_utils import display_graph, chart_signals, h_line

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
