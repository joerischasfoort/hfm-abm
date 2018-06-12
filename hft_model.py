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
        if tick > 331:
            print('tick: ', tick)
        active_traders = random.sample(low_frequency_traders, int((parameters['lft_sample_size'] * len(low_frequency_traders))))
        # select active HFT traders
        all_speed = [hft.var.speed for hft in high_frequency_traders]
        adj_factor = np.divide(1., sum(all_speed))
        relative_speed = [adj_factor * speed for speed in all_speed]
        if high_frequency_traders:
            active_market_makers = np.random.choice(high_frequency_traders,
                                                    size=int((parameters['hft_sample_size'] * len(high_frequency_traders))),
                                                    p=relative_speed, replace=False)
            # sort active market makers to fastest first
            #sorted_active_market_makers = sorted(active_market_makers, key=lambda x: x.var.speed, reverse=False) # can be switched on to take into account hfm speed differences
            sorted_active_market_makers = active_market_makers
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
        #print(fundamental_component)
        noise_component = parameters['std_noise'] * np.random.randn()
        hfm_mr_component = np.cumsum(orderbook.returns[-parameters['hfm_horizon_max']:]
                                           ) / np.arange(1., float(parameters['hfm_horizon_max'] + 1))
        lft_chartist_component = np.cumsum(orderbook.minute_returns[-parameters['horizon_max']:]
                                           ) / np.arange(1., float(parameters['horizon_max'] + 1))
        hfm_smoothed_prices = savitzky_golay(np.array(orderbook.tick_close_price), 41, 7)

        for trader in active_traders:
            # update expectations
            fcast_return = trader.var.forecast_adjust * (trader.var.weight_fundamentalist * fundamental_component + trader.var.weight_chartist *
                                                         lft_chartist_component[trader.par.horizon] + trader.var.weight_random * noise_component)
            fcast_price = lft_mid_price * np.exp(fcast_return)
            # submit orders
            if fcast_price > lft_mid_price:
                bid_price = fcast_price * (1. - trader.par.spread)
                volume = abs(int(np.random.normal(scale=parameters['std_LFT_vol'])))
                orderbook.add_bid(bid_price, volume, trader)
            else:
                ask_price = fcast_price * (1 + trader.par.spread)
                volume = abs(int(np.random.normal(scale=parameters['std_LFT_vol'])))
                orderbook.add_ask(ask_price, volume, trader)

        for market_maker in sorted_active_market_makers:
            # 1 cancel any active orders
            if market_maker.var.active_orders:
                for order in market_maker.var.active_orders:
                    orderbook.cancel_order(order)
                market_maker.var.active_orders = []

            # 2 place new order
            fcast_return = -hfm_mr_component[market_maker.par.horizon] - (parameters['transaction_fee'] * hfm_mid_price)
            fcast_price = hfm_mid_price * np.exp(fcast_return)

            fcast_volatility = np.var(hfm_smoothed_prices[-market_maker.par.horizon * 6:])

            current_stocks = max((market_maker.var.stocks * hfm_mid_price) / market_maker.var.wealth, 0.001) # prevent this from going to zero to find optimum price

            # determine p*: the price at which the hfm would be satisfied with its current portfolio
            def optimal_p_star(price):
                price = abs(price)
                stocks = np.divide(np.log(fcast_price / price),
                                   market_maker.par.risk_aversion * fcast_volatility * price) - current_stocks
                return stocks

            def optimal_stock_holdings(price):
                stocks = np.divide(np.log(fcast_price / price), market_maker.par.risk_aversion * fcast_volatility * price)
                return stocks

            try:
                p_star = float(scipy.optimize.broyden1(optimal_p_star, fcast_price, line_search='wolfe'))
            except:
                p_star = None

            if p_star:
                # quote ask & bid prices
                if orderbook.highest_bid_price + market_maker.par.minimum_price_increment > p_star:
                    bid_price = max(p_star - market_maker.par.minimum_price_increment, 0)
                    bid_volume = int(min(optimal_stock_holdings(bid_price)- market_maker.var.stocks, market_maker.var.money * bid_price))
                    if bid_volume > 0:
                        bid = orderbook.add_bid(bid_price, bid_volume, market_maker)
                        market_maker.var.active_orders.append(bid)
                elif orderbook.highest_bid_price + market_maker.par.minimum_price_increment < p_star:
                    bid_price = orderbook.highest_bid_price + market_maker.par.minimum_price_increment
                    bid_volume = int(min(optimal_stock_holdings(bid_price) - market_maker.var.stocks, market_maker.var.money * bid_price))
                    if bid_volume > 0:
                        bid = orderbook.add_bid(bid_price, bid_volume, market_maker)
                        market_maker.var.active_orders.append(bid)

                if orderbook.lowest_ask_price - market_maker.par.minimum_price_increment > p_star:
                    ask_price = max(orderbook.lowest_ask_price - market_maker.par.minimum_price_increment, 0)
                    ask_volume = int(min(market_maker.var.stocks - optimal_stock_holdings(ask_price), market_maker.var.stocks))
                    if ask_volume > 0:
                        ask = orderbook.add_ask(ask_price, ask_volume, market_maker)
                        market_maker.var.active_orders.append(ask)
                elif orderbook.lowest_ask_price - market_maker.par.minimum_price_increment < p_star:
                    ask_price = max(p_star + market_maker.par.minimum_price_increment, 0)
                    ask_volume = int(min(market_maker.var.stocks - optimal_stock_holdings(ask_price) * market_maker.var.wealth, market_maker.var.stocks)) #TODO check if this works
                    if ask_volume > 0:
                        ask = orderbook.add_ask(ask_price, ask_volume, market_maker)
                        market_maker.var.active_orders.append(ask)

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
