""""The main model"""
import numpy as np
import random
import scipy.optimize
from functions.helpers import savitzky_golay


def hft_model(high_frequency_traders, low_frequency_traders, orderbook, parameters, seed=1):
    """The main model function"""
    random.seed(seed)
    np.random.seed(seed)
    lft_mid_price = orderbook.tick_close_price[-1]
    fundamental = [parameters["fundamental_value"]]

    for tick in range(parameters['horizon_max'] + 1, parameters["ticks"]):
        if tick % 250 == 0:
            print('tick: ', tick)
        active_traders = random.sample(low_frequency_traders, int((parameters['lft_sample_size'] * len(low_frequency_traders))))
        # determine which market maker is active in the tick
        active_market_makers = []

        if high_frequency_traders:
            for hfm in high_frequency_traders:
                # speed determines wether the hfm is active this tick
                if random.random() < hfm.var.speed:
                    active_market_makers.append(hfm)
            # 1 for every hfm determine if they are present in the market
            # select active HFT traders
            if active_market_makers:
                #all_speed = [hft.var.speed for hft in high_frequency_traders]
                #adj_factor = np.divide(1., sum(all_speed))
                #relative_speed = [adj_factor * speed for speed in all_speed]
                # sort active market makers to fastest first
                sorted_active_market_makers = sorted(active_market_makers, key=lambda x: x.var.speed, reverse=False) # can be switched on to take into account hfm speed differences
            #sorted_active_market_makers = active_market_makers
            else:
                sorted_active_market_makers = []
        else:
            sorted_active_market_makers = []

        # re-seed the random number generator after np.random.choice at different lengths
        random.seed(seed + tick)
        np.random.seed(seed + tick)

        # update common LFT price components
        hfm_mid_price = orderbook.tick_close_price[-1]
        if tick % parameters['ticks_per_minute'] == 0:
            lft_mid_price = orderbook.tick_close_price[-1]
            # evolve the fundamental value via AR(1) process
            fundamental.append(fundamental[-1] + parameters["std_fundamental"] * np.random.randn())

        fundamental_component = np.log(fundamental[-1] / lft_mid_price)
        noise_component = parameters['std_noise'] * np.random.randn()
        lft_chartist_component = np.cumsum(orderbook.minute_returns[-parameters['horizon_max']:]
                                           ) / np.arange(1., float(parameters['horizon_max'] + 1))
        hfm_mr_component = np.cumsum(orderbook.returns[-parameters['hfm_horizon_max']:]
                                     ) / np.arange(1., float(parameters['hfm_horizon_max'] + 1))

        # market makers provide quotes
        for market_maker in sorted_active_market_makers:
            # 1 cancel any active quotes
            if market_maker.var.active_orders:
                for order in market_maker.var.active_orders:
                    orderbook.cancel_order(order)
                market_maker.var.active_orders = []

            # 2 make forecasts
            fcast_return = -hfm_mr_component[market_maker.par.horizon] - (parameters['transaction_fee'] * hfm_mid_price)
            fcast_price = hfm_mid_price * np.exp(fcast_return)
            std_history = np.std(orderbook.tick_close_price[-parameters['hfm_horizon_max']:])
            fcast_std = market_maker.var_previous.fcast_std[-1] + market_maker.par.adaptive_param * (std_history - market_maker.var_previous.fcast_std[-1])
            market_maker.var_previous.fcast_std.append(fcast_std)

            # 3 determine bid & ask quotes
            spread = market_maker.par.volatility_sensitivity * fcast_std
            inventory_imbalance = (market_maker.var.stocks - market_maker.par.inventory_target) / market_maker.par.inventory_target
            balancing_var = 1 / (1 + np.exp(-inventory_imbalance))

            potential_bid_price = orderbook.highest_bid_price + market_maker.par.minimum_price_increment
            potential_ask_price = orderbook.lowest_ask_price - market_maker.par.minimum_price_increment
            quote_volume = max(abs(np.random.normal(scale=parameters['std_HFT_vol'])), 1)

            bid_price = min(fcast_price - balancing_var * spread, potential_bid_price)
            bid_volume = int(min(quote_volume, market_maker.var.money / potential_bid_price))
            if bid_volume > 0:
                bid = orderbook.add_bid(bid_price, bid_volume, market_maker)
                market_maker.var_previous.bid_quote.append(bid_price)
                market_maker.var_previous.bid_quote_volume.append(bid_volume)
                market_maker.var.active_orders.append(bid)

            ask_price = max(fcast_price + (1 - balancing_var) * spread, potential_ask_price)
            ask_volume = int(min(quote_volume, market_maker.var.stocks))
            if ask_volume > 0:
                ask = orderbook.add_ask(ask_price, ask_volume, market_maker)
                market_maker.var_previous.ask_quote.append(ask_price)
                market_maker.var_previous.ask_quote_volume.append(ask_volume)
                market_maker.var.active_orders.append(ask)

            if market_maker.var.stocks < 0:
                print('I have negative inventory')

            if market_maker.var.money < 0:
                print('I have negative money')

        # LFTs enter market
        for trader in active_traders:
            # update expectations
            fcast_return = trader.var.forecast_adjust * (trader.var.weight_fundamentalist * fundamental_component + trader.var.weight_chartist *
                                                         lft_chartist_component[trader.par.horizon] + trader.var.weight_random * noise_component)
            fcast_price = lft_mid_price * np.exp(fcast_return)
            # submit orders
            if fcast_price > lft_mid_price:
                bid_price = fcast_price * (1. - trader.par.spread)
                volume = max(1, abs(int(np.random.normal(scale=parameters['std_LFT_vol']))))
                orderbook.add_bid(bid_price, volume, trader)
            else:
                ask_price = fcast_price * (1 + trader.par.spread)
                volume = max(1, abs(int(np.random.normal(scale=parameters['std_LFT_vol']))))
                orderbook.add_ask(ask_price, volume, trader)

        # record market depth before clearing
        orderbook.update_stats()

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
                seller.var_previous.locked_profit.append(locked_profit)
                seller.var.inventory_age = 0
        # Record hft variables
        for hft in high_frequency_traders:
            hft.var_previous.money.append(hft.var.money)
            hft.var_previous.stocks.append(hft.var.stocks)
            hft.var.wealth = hft.var.money + (hft.var.stocks * np.mean([orderbook.highest_bid_price, orderbook.lowest_ask_price]))
            hft.var_previous.wealth.append(hft.var.wealth)
            hft.var.inventory_age += 1

        orderbook.cleanse_book()

        if tick % parameters['ticks_per_minute'] == 0:
            orderbook.update_minute_returns()
            orderbook.fundamental = fundamental

    return high_frequency_traders, low_frequency_traders, orderbook
