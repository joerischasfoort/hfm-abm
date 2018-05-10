import numpy as np


class LFTrader:
    """Class holding low frequency trader properties"""
    def __init__(self, name, variables, previous_variables, parameters, expectations):
        self.name = name
        self.var = variables
        self.var_previous = previous_variables
        self.par = parameters
        self.exp = expectations

    def __repr__(self):
        return 'LFT' + str(self.name)


class Tradervariables:
    """
    Holds the initial variables for the traders
    """
    def __init__(self, money, stocks, weight_fundamentalist, weight_chartist, weight_random):
        self.money = money
        self.stocks = stocks
        self.weight_fundamentalist = abs(np.random.laplace(0., weight_fundamentalist))#weight_fundamentalist * np.random.randn())
        self.weight_chartist = abs(np.random.laplace(0., weight_chartist))#(weight_chartist * np.random.randn())
        self.weight_random = abs(np.random.laplace(0., weight_random))#(weight_random * np.random.randn())
        self.forecast_adjust = 1. / (self.weight_fundamentalist + self.weight_chartist + self.weight_random)
        self.last_buy_price = {'price': 0, 'age': 0}


class TraderParameters:
    """
    Holds the the trader parameters
    """
    def __init__(self, horizon_min, horizon_max, max_spread):
        self.horizon_min = horizon_min
        self.horizon_max = horizon_max
        self.horizon = np.random.randint(horizon_min, horizon_max)
        self.spread = max_spread * np.random.rand()


class TraderExpectations:
    """
    Holds the agent expectations for several variables
    """
    def __init__(self, price):
        self.price = price


class HFTrader:
    """Class holding high frequency trader properties"""
    def __init__(self, name, variables, previous_variables, parameters):
        self.name = name
        self.var = variables
        self.var_previous = previous_variables
        self.par = parameters

    def __repr__(self):
        return 'HFT' + str(self.name)


class HFTvariables:
    """
    Holds the initial variables for the traders
    """
    def __init__(self, money, stocks, speed, cum_investment, wealth, last_buy_price):
        self.money = money
        self.stocks = stocks
        self.speed = speed
        self.cum_investment = cum_investment
        self.wealth = wealth
        self.last_buy_price = last_buy_price
        self.inventory_age = 0
        self.active_orders = []


class HFTParameters:
    """
    Holds the the trader parameters
    """
    def __init__(self, inventory_target, minimum_price_increment, investment_fraction, risk_aversion):
        self.inventory_target = inventory_target
        self.minimum_price_increment = minimum_price_increment
        self.investment_fraction = investment_fraction
        self.risk_aversion = risk_aversion


class HFTHistory:
    """
    Holds the the market maker history values of interest
    """

    def __init__(self, money, stocks, speed, cum_investment, wealth):
        self.money = [money]
        self.stocks = [stocks]
        self.speed = [speed]
        self.cum_investment = [cum_investment]
        self.wealth = [wealth]
        self.locked_profit = []
