import numpy as np

class LFTrader():
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
    def __init__(self, wealth, weight_fundamentalist, weight_chartist, weight_random):
        self.wealth = wealth
        self.weight_fundamentalist = np.abs(weight_fundamentalist * np.random.randn())
        self.weight_chartist = (weight_chartist * np.random.randn())
        self.weight_random = (weight_random * np.random.randn())
        self.forecast_adjust = 1. / (self.weight_fundamentalist + self.weight_chartist + self.weight_random)


class TraderParameters:
    """
    Holds the the trader parameters
    """
    def __init__(self, horizon_min, horizon_max):
        self.horizon_min = horizon_min
        self.horizon_max = horizon_max
        self.horizon = np.random.randint(horizon_min, horizon_max)


class TraderExpectations:
    """
    Holds the agent expectations for several variables
    """
    def __init__(self, price):
        self.price = price


class HFTrader():
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
    def __init__(self, money, inventory):
        self.money = money
        self.inventory = inventory


class HFTParameters:
    """
    Holds the the trader parameters
    """
    def __init__(self, inventory_target, minimum_price_increment):
        self.inventory_target = inventory_target
        self.minimum_price_increment = minimum_price_increment