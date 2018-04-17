""""The main model"""
import numpy as np
import random


def hft_model(high_frequency_traders, low_frequency_traders, orderbook, parameters, seed=1):
    """The main model function"""
    random.seed(seed)
    np.random.seed(seed)

    for tick in range(parameters['av_return_interval_max'] + 1, parameters["ticks"]):
        active_traders = random.sample(low_frequency_traders, int((parameters['lft_sample_size'] * len(low_frequency_traders))))
        # TODO add select faster market makers with a higher probability
        active_market_makers = random.sample(high_frequency_traders, int((parameters['hft_sample_size'] * len(high_frequency_traders))))
        # update common LFT price components
        mid_price = 0.5 * (orderbook.highest_bid_price + orderbook.lowest_ask_price)
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
                orderbook.add_bid(mid_price + np.random.normal(scale=parameters['std_LFT_price']),
                                  abs(int(np.random.normal(scale=parameters['std_LFT_vol']))), trader)
            else:
                orderbook.add_ask(mid_price + np.random.normal(scale=parameters['std_LFT_price']),
                                  abs(int(np.random.normal(scale=parameters['std_LFT_vol']))), trader)

        for market_maker in active_market_makers:
            volume = abs(market_maker.var.stocks - market_maker.par.inventory_target + int(np.random.normal(scale=parameters['std_HFT_vol'])))
            if market_maker.var.stocks > market_maker.par.inventory_target:#TODO add reference to total money? :
                orderbook.add_ask(orderbook.lowest_ask_price - market_maker.par.minimum_price_increment,
                                  volume, market_maker)
            else:
                orderbook.add_bid(orderbook.highest_bid_price + market_maker.par.minimum_price_increment,
                                  volume, market_maker)

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

        orderbook.cleanse_book()

    return high_frequency_traders, low_frequency_traders, orderbook
