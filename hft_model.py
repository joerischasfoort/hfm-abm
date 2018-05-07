""""The main model"""
import numpy as np
import random


def hft_model(high_frequency_traders, low_frequency_traders, orderbook, parameters, seed=1):
    """The main model function"""
    random.seed(seed)
    np.random.seed(seed)

    for tick in range(parameters['av_return_interval_max'] + 1, parameters["ticks"]):
        if tick % parameters["investment_frequency"] == 0:
            # investment
            for hft in high_frequency_traders:
                investment_amount = max(hft.par.investment_fraction * hft.var.money, 0)
                hft.var.cum_investment += investment_amount
                hft.var.money -= investment_amount
                hft.var.speed = parameters["hft_speed"] + hft.var.cum_investment**parameters["return_on_investment"]
                # update hft speed & cum_investment
                hft.var_previous.speed.append(hft.var.speed)
                hft.var_previous.cum_investment.append(hft.var.cum_investment)

        # select active traders
        active_traders = random.sample(low_frequency_traders, int((parameters['lft_sample_size'] * len(low_frequency_traders))))
        # select active HFT traders
        all_speed = [hft.var.speed for hft in high_frequency_traders]
        adj_factor = np.divide(1., sum(all_speed))
        relative_speed = [adj_factor * speed for speed in all_speed]
        try:
            active_market_makers = np.random.choice(high_frequency_traders,
                                                    size=int((parameters['hft_sample_size'] * len(high_frequency_traders))),
                                                    p=relative_speed, replace=False)
            # sort active market makers to fastest first
            sorted_active_market_makers = sorted(active_market_makers, key=lambda x: x.var.speed, reverse=False)
        except:
            sorted_active_market_makers = []

        # update common LFT price components
        mid_price = orderbook.tick_close_price[-1]
        fundamental_component = np.log(parameters['fundamental_value'] / mid_price)
        noise_component = parameters['std_noise'] * np.random.randn()
        chartist_component = np.cumsum(orderbook.returns[-parameters['av_return_interval_max']:]
                                       ) / np.arange(1., float(parameters['av_return_interval_max'] + 1))

        for trader in active_traders:
            # update expectations
            fcast_return = trader.var.forecast_adjust * (trader.var.weight_fundamentalist * fundamental_component + trader.var.weight_chartist *
                                                 chartist_component[trader.par.horizon] + trader.var.weight_random * noise_component)
            fcast_return = min(fcast_return, 0.5)
            fcast_return = max(fcast_return, -0.5)
            fcast_price = mid_price * np.exp(fcast_return)
            # submit orders
            if fcast_price > mid_price:
                bid_price = fcast_price * (1. - trader.par.spread)
                orderbook.add_bid(bid_price, abs(int(np.random.normal(scale=parameters['std_LFT_vol']))), trader)
            else:
                ask_price = fcast_price * (1 + trader.par.spread)
                orderbook.add_ask(ask_price, abs(int(np.random.normal(scale=parameters['std_LFT_vol']))), trader)

        for market_maker in sorted_active_market_makers:
            # cancel any active orders
            if market_maker.var.active_orders:
                for order in market_maker.var.active_orders:
                    orderbook.cancel_order(order)

            # place new order
            ideal_volume = parameters['hfm_fixed_vol']
            if market_maker.var.inventory_age > market_maker.par.risk_aversion:
                price = orderbook.lowest_ask_price - market_maker.par.minimum_price_increment
                volume = int(min(ideal_volume, market_maker.var.stocks))
                ask = orderbook.add_ask(price, volume, market_maker)
                market_maker.var.active_orders.append(ask)
            elif market_maker.var.stocks > market_maker.par.inventory_target:#TODO add reference to total money?:
                price = orderbook.lowest_ask_price - market_maker.par.minimum_price_increment
                volume = int(min(ideal_volume, market_maker.var.stocks)) # inventory constraint
                if volume > 0 and price > market_maker.var.last_buy_price['price']:
                    ask = orderbook.add_ask(price, volume, market_maker)
                    market_maker.var.active_orders.append(ask)
            else:
                price = orderbook.highest_bid_price + market_maker.par.minimum_price_increment
                volume = int(min(ideal_volume, market_maker.var.money / price)) # budget constraint
                if volume > 0:
                    bid = orderbook.add_bid(price, volume, market_maker)
                    market_maker.var.active_orders.append(bid)

        while True:
            matched_orders = orderbook.match_orders()
            if matched_orders is None:
                break
            # execute trade
            buyer, seller = matched_orders[2].owner, matched_orders[3].owner
            buyer.var.stocks += matched_orders[1]
            seller.var.stocks -= matched_orders[1]
            buyer.var.money -= matched_orders[0] * matched_orders[1]
            seller.var.money += matched_orders[0] * matched_orders[1]
            # record last buy price for HFT traders
            if "HFT" in repr(buyer):
                buyer.var.last_buy_price['price'] = matched_orders[0]
                #buyer.var.last_buy_price['age'] = 0
            if "HFT" in repr(seller):
                locked_profit = matched_orders[0] - seller.var.last_buy_price['price']
                print(locked_profit)
                seller.var_previous.locked_profit.append(locked_profit)
                seller.var.inventory_age = 0
        # Record hft variables
        for hft in high_frequency_traders:
            hft.var_previous.money.append(hft.var.money)
            hft.var_previous.stocks.append(hft.var.stocks)
            hft.var_previous.wealth.append(hft.var.wealth)
            hft.var.inventory_age += 1
            # update last_buy_price age and reset if age is over risk aversion limit
            # hft.var.last_buy_price['age'] += 1
            # if hft.var.last_buy_price['age'] > hft.par.risk_aversion:
            #     hft.var.last_buy_price['price'] = 0
            #     hft.var.last_buy_price['age'] = 0

        orderbook.cleanse_book()

    return high_frequency_traders, low_frequency_traders, orderbook
