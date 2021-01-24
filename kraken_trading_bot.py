import krakenex
from pykrakenapi import KrakenAPI

from trading_bot import Dispatcher, TradingBot, timestamp
import numpy as np

from indicators import *

import threading


class KrakenDispatcher(Dispatcher):
    def __init__(self, interval=5, pairs=[], stop_loss_min_perc=1, stop_loss_max_perc=3, take_profit_max_perc=8):
        self.interval = interval
        self.data = {}
        self.last = None

        self.pairs = pairs
        self.ticker_info = {}

        self.buys = {}
        self.sells = {}
        self.winning_trades = 0
        self.trades = 0

        self.stop_loss_min_perc = stop_loss_min_perc
        self.stop_loss_max_perc = stop_loss_max_perc
        self.take_profit_max_perc = take_profit_max_perc

        self.sell_lock = threading.Lock()

        self.positions = {}
        self.userrefs = {pair: i+1 for i, pair in enumerate(pairs)}

        self.api = krakenex.API()
        self.api.load_key('kraken.key')

        self.kraken = KrakenAPI(self.api)

        self.balance = None
        self.pnl = 0

    def print_status(self):
        print("%s Balance: %s\nPnL: %f" % (timestamp(), str(self.balance), self.pnl))

    def get_userref(self, pair):
        return self.userrefs[pair]

    def buy(self, pair):
        if self.balance is not None and pair in self.ticker_info:
            ask = self.current_ask_price(pair)

            quote = self.pairs.loc[pair]['quote']
            amount = int(self.balance.loc[quote]['vol'] / ask)

            ordermin = float(self.pairs.loc[pair]['ordermin'])
            if amount < ordermin:
                print("Minimum order %d %s" % (ordermin, pair))
                return

            if self.balance.loc[quote]['vol'] >= amount * ask:
                print("%s Buying %f %s at price %f" % (timestamp(), amount, pair, ask))

                vol = volatility(self.data[pair])
                print("VOLATILITY %f" % vol)

                userref = self.get_userref(pair)

                # Add a buy order at market price. When closed, add a stop-loss order
                res = self.kraken.add_standard_order(
                    pair, 'buy', 'market', '%f' % amount,
                    close_ordertype='stop-loss',
                    userref='%d' % userref,
                    validate=False,
                    close_price='-%f%%' % (self.stop_loss_min_perc + (self.stop_loss_max_perc - self.stop_loss_min_perc)*vol))
                print("Order made: %s" % str(res))

                self.positions[pair] = {
                    'price': ask,
                    'amount': amount,
                    'take-profit': ask*(1.005+vol*self.take_profit_max_perc/100)}
                print("%s: %s" % (pair, str(self.positions[pair])))

                self.buys[pair][-1] = ask

                self.print_status()
                print("")
            else:
                print("Balance too low to buy %f %s at price %f" % (amount, pair, ask))

    def sell(self, pair):
        if self.balance is not None and pair in self.ticker_info:
            bid = self.current_bid_price(pair)

            base = self.pairs.loc[pair]['base']

            amount = int(self.balance.loc[base]['vol'])

            ordermin = float(self.pairs.loc[pair]['ordermin'])
            if amount < ordermin:
                print("Minimum order %d %s" % (ordermin, pair))
                return

            if self.balance.loc[base]['vol'] >= amount:
                print("%s Selling %f %s at price %f" % (timestamp(), amount, pair, bid))

                userref = self.get_userref(pair)

                # Add a sell order at market price. When closed, add a stop-loss order

                # Cancel all other open orders for this pair
                self.kraken.cancel_open_order('%d' % userref)
                res = self.kraken.add_standard_order(
                    pair, 'sell', 'market', '%d' % amount,
                    userref='%d' % userref,
                    validate=False)
                print("Order made: %s" % str(res))

                if pair in self.positions:
                    profit = self.positions[pair]['amount'] * (bid - self.positions[pair]['price'])
                    self.pnl += profit
                    if profit > 0:
                        self.winning_trades += 1
                    del self.positions[pair]

                self.sells[pair][-1] = bid
                self.trades += 1

                self.print_status()
                print("")
            else:
                print("Balance too low to sell %f %s at price %f" % (amount, pair, bid))

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
        # print("PAIR %s ASK: %s BID: %s" % (pair, ask, bid))

        self.ticker_info[pair] = {'ask': ask, 'bid': bid}

        if pair in self.positions:
            position = self.positions[pair]
            if position['take-profit'] <= bid:
                print("Takeprofit activated for %s" % (str(position)))
                # Cancel all other open orders for this pair
                self.kraken.cancel_open_order('%d' % self.get_userref(pair))
                self.sell(pair)


def KrakenTradingBot(pairs, interval):
    dispatcher = KrakenDispatcher(interval=interval, pairs=pairs)
    bot = TradingBot(dispatcher, pairs=pairs)

    asset_pairs = dispatcher.kraken.get_tradable_asset_pairs(pair=','.join(pairs))
    bot.dispatcher.pairs = asset_pairs[['ordermin', 'wsname', 'quote', 'base']]

    ws_names = asset_pairs['wsname']

    import websocket
    import _thread
    import json

    ws_channels = {}

    token = dispatcher.api.query_private('GetWebSocketsToken')['result']['token']

    # Define WebSocket callback functions
    def ws_message(ws, message):
        j = json.loads(message)
        if 'channelID' in j:
            ws_channels[j['channelID']] = {'pair': j['pair'], 'subscription':j['subscription']}

        if '[' == message[0]:
            cID = j[0]
            pair = ws_names[ws_names == j[-1]].index[0]
            if ws_channels[cID]['subscription']['name'] == 'ticker':
                bot.dispatcher.update_ticker(pair, j)

    def ws_open(ws):
        for pair in ws_names.array:
            ws.send('{"event":"subscribe", "subscription":{"name":"ticker"}, "pair":["%s"]}' % (pair))

    def ws_auth_open(ws):
        ws.send('{"event":"subscribe", "subscription":{"name":"openOrders", "token":"%s"} }' % (token))

    def ws_auth_message(ws, message):
        j = json.loads(message)
        if '[' == message[0]:
            # Update balance once every time openOrders changes status
            if j[1] == 'openOrders':
                bot.dispatcher.balance = dispatcher.kraken.get_account_balance()
                print(message)

    def ws_thread(*args):
        print("Connecting to public WebSocket API")
        ws = websocket.WebSocketApp("wss://ws.kraken.com/", on_open=ws_open, on_message=ws_message)
        ws.run_forever()

    def ws_auth_thread(*args):
        print("Connecting to private WebSocket API")
        ws = websocket.WebSocketApp("wss://ws-auth.kraken.com/", on_open=ws_auth_open, on_message=ws_auth_message)
        ws.run_forever()

    # Start a new thread for the WebSocket interface
    _thread.start_new_thread(ws_thread, ())
    _thread.start_new_thread(ws_auth_thread, ())

    return bot


if __name__ == '__main__':
    bot = KrakenTradingBot(pairs=['ADAEUR'], interval=1)
    try:
        bot.strategy_2()
    except KeyboardInterrupt:
        print("Done")

        # from chart_utils import display_graph, chart_signals, h_line

        print('%d Trades made. %d Winners. %f%% Winners. %f%% %s'
              % (bot.dispatcher.trades,
                 bot.dispatcher.winning_trades,
                 100*bot.dispatcher.winning_trades/bot.dispatcher.trades if bot.dispatcher.trades > 0 else 0,
                 100*(bot.dispatcher.pnl/1000),
                 "up" if bot.dispatcher.pnl > 0 else "down"))
