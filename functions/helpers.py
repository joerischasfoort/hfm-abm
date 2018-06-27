import numpy as np
import pandas as pd
from math import factorial


def div0(a, b):
    """
    ignore / 0, and return 0 div0( [-1, 0, 1], 0 ) -> [0, 0, 0]
    credits to Dennis @ https://stackoverflow.com/questions/26248654/numpy-return-0-with-divide-by-zero
    """
    answer = np.true_divide(a, b)
    if not np.isfinite(answer):
        answer = 0
    return answer


def savitzky_golay(y, window_size, order, deriv=0, rate=1):
    r"""Smooth (and optionally differentiate) data with a Savitzky-Golay filter.
    The Savitzky-Golay filter removes high frequency noise from data.
    It has the advantage of preserving the original shape and
    features of the signal better than other types of filtering
    approaches, such as moving averages techniques.
    Parameters
    ----------
    y : array_like, shape (N,)
        the values of the time history of the signal.
    window_size : int
        the length of the window. Must be an odd integer number.
    order : int
        the order of the polynomial used in the filtering.
        Must be less then `window_size` - 1.
    deriv: int
        the order of the derivative to compute (default = 0 means only smoothing)
    Returns
    -------
    ys : ndarray, shape (N)
        the smoothed signal (or it's n-th derivative).
    Notes
    -----
    The Savitzky-Golay is a type of low-pass filter, particularly
    suited for smoothing noisy data. The main idea behind this
    approach is to make for each point a least-square fit with a
    polynomial of high order over a odd-sized window centered at
    the point.
    Examples
    --------
    t = np.linspace(-4, 4, 500)
    y = np.exp( -t**2 ) + np.random.normal(0, 0.05, t.shape)
    ysg = savitzky_golay(y, window_size=31, order=4)
    import matplotlib.pyplot as plt
    plt.plot(t, y, label='Noisy signal')
    plt.plot(t, np.exp(-t**2), 'k', lw=1.5, label='Original signal')
    plt.plot(t, ysg, 'r', label='Filtered signal')
    plt.legend()
    plt.show()
    References
    ----------
    .. [1] A. Savitzky, M. J. E. Golay, Smoothing and Differentiation of
       Data by Simplified Least Squares Procedures. Analytical
       Chemistry, 1964, 36 (8), pp 1627-1639.
    .. [2] Numerical Recipes 3rd Edition: The Art of Scientific Computing
       W.H. Press, S.A. Teukolsky, W.T. Vetterling, B.P. Flannery
       Cambridge University Press ISBN-13: 9780521880688
    """
    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(order))
    except ValueError:
        raise ValueError("window_size and order have to be of type int")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    order_range = range(order + 1)
    half_window = (window_size - 1) // 2
    # precompute coefficients
    b = np.mat([[k ** i for i in order_range] for k in range(-half_window, half_window + 1)])
    m = np.linalg.pinv(b).A[deriv] * rate ** deriv * factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - np.abs(y[1:half_window + 1][::-1] - y[0])
    lastvals = y[-1] + np.abs(y[-half_window - 1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve(m[::-1], y, mode='valid')


def organise_data(obs):
    """
    Helper function to organise orderbook data output from multiple monte-carlo simulations
    :param obs: list of orderbooks
    :return: pandas DataFrames of prices, returns, autocorrelations, volatility, volume & fundamentals
    """
    window = 20
    close_price = []
    returns = []
    autocorr_returns = []
    autocorr_abs_returns = []
    returns_volatility = []
    volume = []
    fundamentals = []
    for ob in obs:  # record
        # close price
        close_price.append(ob.tick_close_price)
        # returns
        r = pd.Series(np.array(ob.tick_close_price)).pct_change()
        returns.append(r)
        # autocorrelation returns
        ac_r = [r.autocorr(lag=lag) for lag in range(25)]
        autocorr_returns.append(ac_r)
        # autocorrelation absolute returns
        absolute_returns = pd.Series(r).abs()
        autocorr_abs_returns.append([absolute_returns.autocorr(lag=lag) for lag in range(25)])
        # volatility of returns
        roller_returns = r.rolling(window)
        returns_volatility.append(roller_returns.std(ddof=0))
        # volume
        volume.append([sum(volumes) for volumes in ob.transaction_volumes_history])
        # fundamentals
        fundamentals.append(ob.fundamental)
    mc_prices = pd.DataFrame(close_price).transpose()
    mc_returns = pd.DataFrame(returns).transpose()
    mc_autocorr_returns = pd.DataFrame(autocorr_returns).transpose()
    mc_autocorr_abs_returns = pd.DataFrame(autocorr_abs_returns).transpose()
    mc_volatility = pd.DataFrame(returns_volatility).transpose()
    mc_volume = pd.DataFrame(volume).transpose()
    mc_fundamentals = pd.DataFrame(fundamentals).transpose()

    return mc_prices, mc_returns, mc_autocorr_returns, mc_autocorr_abs_returns, mc_volatility, mc_volume, mc_fundamentals


def hft_in_match(match):
    """
    Check if a high frequency trader was a counterparty in at least one of two matched orders
    :param match: tuple of a bid and ask order matched by the limit-order book
    :return: Boolean True or False
    """
    for buy_sell in match:
        if 'HFT' in str(buy_sell):
            return True
    return False


def prcnt_hft_trading(ob):
    """
    Find out the total percentage of trades in which a high frequency trader partook
    :param ob: Object orderbook
    :return: float percentage of traders
    """
    amount_matched_orders = 0
    hft_participating_orders = 0
    for tick in ob.matched_bids_history:
        amount_matched_orders += len(tick)
        for match in tick:
            if hft_in_match(match):
                hft_participating_orders += 1

    percentage_hft_matches = hft_participating_orders / amount_matched_orders
    return percentage_hft_matches


def sharpe(periods, mean, standard_deviation):
    """
    Calculate sharpe ratio
    :param periods: int total periods over which to make the calculation
    :param mean: float average value
    :param standard_deviation: float standard deviation of value
    :return: float Sharpe Ratio
    """
    return np.sqrt(periods) * (mean / standard_deviation)


def all_sharpe(hfts):
    """

    :param hfts:
    :return:
    """
    money = []
    stocks = []
    locked_in_profits = []
    for hft in hfts:
        money.append(np.array(hft.var_previous.money))
        stocks.append(np.array(hft.var_previous.stocks))
        locked_in_profits.append(np.array(hft.var_previous.locked_profit))
    all_profits = np.concatenate(locked_in_profits)
    all_sharpe = sharpe(len(all_profits), all_profits.mean(), all_profits.std())
    return all_sharpe


def av_bid_asks(orderbooks):
    mean_bid_asks = []
    for ob in orderbooks:
        bid_ask = [ask - bid for bid, ask in zip(ob.highest_bid_price_history, ob.lowest_ask_price_history)]
        # quoted bid_ask_spread = (Ask - Bid / Mid) / 2
        bid_ask = list(filter(lambda x: x >0, bid_ask))
        mean_bid_asks.append(np.mean(bid_ask))
    return mean_bid_asks


def depth(orderbooks):
    average_depth = []
    average_imbalance = []
    for ob in orderbooks:
        av_ask_depth = np.mean(ob.tick_bid_depth) #[np.mean(prices) for prices in orderbook.transaction_prices_history]
        av_bid_depth = np.mean(ob.tick_ask_depth)
        average_imbalance.append(np.mean(abs(np.array(ob.tick_bid_depth) - np.array(ob.tick_ask_depth))))
        average_depth.append(av_ask_depth + av_bid_depth)
    return average_depth, average_imbalance


def vol(orderbooks):
    volume = []
    for ob in orderbooks:
        total_tick_volume = [sum(volumes) for volumes in ob.transaction_volumes_history]
        volume.append(sum(total_tick_volume))
    return volume


def vola(orderbooks):
    volatility = []
    for ob in orderbooks:
        end_tick_price = ob.tick_close_price #[np.mean(prices) for prices in orderbook.transaction_prices_history]
        returns = pd.Series(np.array(end_tick_price)).pct_change()
        volatility.append(returns.std())
    return volatility