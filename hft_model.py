""""The main model"""
import numpy as np
import random


def hft_model(high_frequency_traders, low_frequency_traders, orderbook, parameters, seed=1):
    """The main model function"""
    random.seed(seed)
    np.random.seed(seed)
    lft_mid_price = orderbook.tick_close_price[-1]
    fundamental = [parameters["fundamental_value"]]

    for tick in range(parameters['horizon_max'] + 1, parameters["ticks"]):
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
        hfm_mid_price = orderbook.tick_close_price[-1]
        if tick % parameters['ticks_per_minute'] == 0:
            lft_mid_price = orderbook.tick_close_price[-1]
            # evolve the fundamental value via AR(1) process
            fundamental.append(fundamental[-1] + parameters["std_fundamental"] * np.random.randn())
        fundamental_component = np.log(fundamental[-1] / lft_mid_price)
        noise_component = parameters['std_noise'] * np.random.randn()
        hfm_mr_component = np.cumsum(orderbook.returns[-parameters['hfm_horizon_max']:]
                                           ) / np.arange(1., float(parameters['hfm_horizon_max'] + 1))
        lft_chartist_component = np.cumsum(orderbook.minute_returns[-parameters['horizon_max']:]
                                           ) / np.arange(1., float(parameters['horizon_max'] + 1))

        for trader in active_traders:
            # update expectations
            fcast_return = trader.var.forecast_adjust * (trader.var.weight_fundamentalist * fundamental_component + trader.var.weight_chartist *
                                                         lft_chartist_component[trader.par.horizon] + trader.var.weight_random * noise_component)
            #fcast_return = min(fcast_return, 0.5)
            #fcast_return = max(fcast_return, -0.5)
            fcast_price = lft_mid_price * np.exp(fcast_return)
            # submit orders
            if fcast_price > lft_mid_price:
                bid_price = fcast_price * (1. - trader.par.spread)
                orderbook.add_bid(bid_price, abs(int(np.random.normal(scale=parameters['std_LFT_vol']))), trader)
            else:
                ask_price = fcast_price * (1 + trader.par.spread)
                orderbook.add_ask(ask_price, abs(int(np.random.normal(scale=parameters['std_LFT_vol']))), trader)

        for market_maker in sorted_active_market_makers:
            # 1 cancel any active orders
            if market_maker.var.active_orders:
                for order in market_maker.var.active_orders:
                    orderbook.cancel_order(order)
                market_maker.var.active_orders = []

            # 2 place new order
            ideal_volume = parameters['hfm_fixed_vol']
            fcast_return = -hfm_mr_component[market_maker.par.horizon]
            # fcast_return = min(fcast_return, 0.5)
            # fcast_return = max(fcast_return, -0.5)
            fcast_price = hfm_mid_price * np.exp(fcast_return)
            if fcast_price > hfm_mid_price:
                bid_price = orderbook.highest_bid_price + market_maker.par.minimum_price_increment
                volume = int(min(ideal_volume, bid_price * market_maker.var.money))
                if volume > 0:
                    bid = orderbook.add_bid(bid_price, volume, market_maker)
                    market_maker.var.active_orders.append(bid)
            else:
                ask_price = orderbook.lowest_ask_price - market_maker.par.minimum_price_increment
                volume = int(min(ideal_volume, market_maker.var.stocks))
                if volume > 0:
                    ask = orderbook.add_ask(ask_price, volume, market_maker)
                    market_maker.var.active_orders.append(ask)

        # record market depth before clearing
        orderbook.update_depth()

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

        if tick % parameters['ticks_per_minute'] == 0:
            orderbook.update_minute_returns()
            orderbook.fundamental = fundamental

    return high_frequency_traders, low_frequency_traders, orderbook
