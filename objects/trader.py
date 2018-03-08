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


class Traderariables:
    """
    Holds the initial variables for the traders
    """
    def __init__(self, wealth, weight_fundamentalist, weight_chartist, weight_random):
        self.wealth = wealth
        self.weight_fundamentalist = weight_fundamentalist
        self.weight_chartist = weight_chartist
        self.weight_random = weight_random


class TraderParameters:
    """
    Holds the the trader parameters
    """
    def __init__(self, ma_short, ma_long):
        self.ma_short = ma_short
        self.ma_long = ma_long


class TraderExpectations:
    """
    Holds the agent expectations for several variables
    """
    def __init__(self, price):
        self.price = price
