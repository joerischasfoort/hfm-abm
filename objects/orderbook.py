"""Limit orderbook updated from Schasfoort & Stockermans 2017"""

import bisect
import operator
import numpy as np

class LimitOrderBook:
    """Base limit order book """
    def __init__(self, last_price, spread_max, max_return_interval, order_expiration):
        self.transaction_prices = []
        self.transaction_volumes = []
        self.matched_bids = []
        self.bids = []
        self.asks = []
        self.order_expiration = order_expiration
        self.unresolved_orders_history = []
        self.transaction_prices_history = []
        self.transaction_volumes_history = []
        self.matched_bids_history = []
        self.highest_bid_price = last_price - (spread_max / 2)
        self.highest_bid_price_history = []
        self.lowest_ask_price = last_price + (spread_max / 2)
        self.lowest_ask_price_history = []
        self.m_m_orders_available_after_cleaning = False
        self.sell_orders_today = 0
        self.buy_orders_today = 0
        self.sell_orders_history = []
        self.buy_orders_history = []
        self.returns = [0 for i in range(max_return_interval)]
        self.minute_returns = [0 for i in range(max_return_interval)]
        self.tick_close_price = [np.mean([self.highest_bid_price, self.lowest_ask_price])]
        self.minute_close_price = [self.tick_close_price[-1]]
        self.tick_bid_depth = []
        self.tick_ask_depth = []
        self.fundamental = []

    def add_bid(self, price, volume, agent):
        """Add a bid to the (price low-high, age young-old) sorted bids book"""
        bid = Order(order_type='b', owner=agent, price=price, volume=volume)
        bisect.insort_left(self.bids, bid)
        self.update_bid_ask_spread('bid')
        return bid

    def add_ask(self, price, volume, agent):
        """Add an ask to the (price low-high, age old-young) sorted asks book"""
        ask = Order(order_type='a', owner=agent, price=price, volume=volume)
        bisect.insort_right(self.asks, ask)
        self.update_bid_ask_spread('ask')
        return ask

    def cancel_order(self, order):
        for book in [self.bids, self.asks]:
            if order in book:
                book.remove(order)

    def cleanse_book(self):
        """
        store and clean unresolved orders
        :return: None
        """
        if len(self.transaction_prices):
            self.transaction_prices_history.append(self.transaction_prices)
        self.transaction_prices = []
        # store and clean recorded transaction volumes
        self.transaction_volumes_history.append(self.transaction_volumes)
        self.transaction_volumes = []
        # store and clean matched bids
        self.matched_bids_history.append(self.matched_bids)
        self.matched_bids = []
        # record the total bids and asks submitted that day
        self.buy_orders_history.append(self.buy_orders_today)
        self.buy_orders_today = 0
        self.sell_orders_history.append(self.sell_orders_today)
        self.sell_orders_today = 0
        # increase the age of orders
        for book in [self.bids, self.asks]:
            for order in book:
                order.age += 1
                if order.age > self.order_expiration:
                    book.remove(order)
        # update current highest bid and lowest ask
        for order_type in ['bid', 'ask']:
            self.update_bid_ask_spread(order_type)
        self.tick_close_price.append(np.mean([self.highest_bid_price, self.lowest_ask_price]))
        self.returns.append((self.tick_close_price[-1] - self.tick_close_price[-2]) / self.tick_close_price[-2])

    def update_minute_returns(self):
        self.minute_close_price.append(self.tick_close_price[-1])
        self.minute_returns.append((self.minute_close_price[-1] - self.minute_close_price[-2]) / self.minute_close_price[-2])

    def match_orders(self):
        """Return a price, volume, bid and ask and delete them from the order book if volume of either reaches zero"""
        # first make sure that neither the bids or asks books are empty
        if not (self.bids and self.asks):
            return None
        # then match highest bid with lowest ask
        if self.bids[-1].price >= self.asks[0].price:
            winning_bid = self.bids[-1]
            winning_ask = self.asks[0]
            price = winning_ask.price
            # volume is the min of the bid and ask, # both bid and ask are then reduced by that volume, if 0, then removed
            min_index, volume = min(enumerate([winning_bid.volume, winning_ask.volume]), key=operator.itemgetter(1))
            if winning_bid.volume == winning_ask.volume:
                # notify owner it no longer has an order in the market
                for order in [winning_bid, winning_ask]:
                    if 'HFT' in repr(order.owner):
                        order.owner.var.active_orders = []#.remove(order)
                # remove these elements from list
                del self.bids[-1]
                del self.asks[0]
                # update current highest bid and lowest ask
                for order_type in ['bid', 'ask']:
                    self.update_bid_ask_spread(order_type)
            else:
                # decrease volume for both bid and ask
                self.asks[0].volume -= volume
                self.bids[-1].volume -= volume
                # delete the empty bid or ask
                if min_index == 0:
                    if 'HFT' in repr(self.bids[-1].owner):
                        self.bids[-1].owner.var.active_orders = []#.remove(self.bids[-1])
                    del self.bids[-1]
                    # update current highest bid
                    self.update_bid_ask_spread('bid')
                else:
                    if 'HFT' in repr(self.asks[0].owner):
                        self.asks[0].owner.var.active_orders = []#.remove(self.asks[0])
                    del self.asks[0]
                    # update lowest ask
                    self.update_bid_ask_spread('ask')
            self.transaction_prices.append(price)
            self.transaction_volumes.append(volume)
            self.matched_bids.append((winning_bid, winning_ask))

            return price, volume, winning_bid, winning_ask

    def update_bid_ask_spread(self, order_type):
        """update the current highest bid or lowest ask and store previous values"""
        if ('ask' not in order_type) and ('bid' not in order_type):
            raise ValueError("unknown order_type")

        if order_type == 'ask' and self.asks:
            #self.lowest_ask_price_history.append(self.lowest_ask_price)
            #self.highest_bid_price_history.append(self.highest_bid_price)
            self.lowest_ask_price = self.asks[0].price
        if order_type == 'bid' and self.bids:
            #self.highest_bid_price_history.append(self.highest_bid_price)
            #self.lowest_ask_price_history.append(self.lowest_ask_price)
            self.highest_bid_price = self.bids[-1].price

    def update_stats(self):
        bid_depth = 0
        ask_depth = 0
        for bid in self.bids:
            bid_depth += bid.volume
        for ask in self.asks:
            ask_depth += ask.volume
        self.tick_bid_depth.append(bid_depth)
        self.tick_ask_depth.append(ask_depth)

        self.lowest_ask_price_history.append(self.lowest_ask_price)
        self.highest_bid_price_history.append(self.highest_bid_price)

    def __repr__(self):
        return "order_book_{}".format(self.stock)


class Order:
    """The order class can represent both bid or ask type orders"""
    def __init__(self, order_type, owner, price, volume):
        """order_type = 'b' for bid or 'a' for ask"""
        self.order_type = order_type
        self.owner = owner
        self.price = price
        self.volume = volume
        self.age = 0

    def __lt__(self, other):
        """Allows comparison to other orders based on price"""
        return self.price < other.price

    def __repr__(self):
        return 'Order_p={}_t={}_o={}_a={}'.format(self.price, self.order_type, self.owner, self.age)
