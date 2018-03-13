import numpy as np
from objects.trader import *


def init_objects(parameters):
    """
    Function to initialise the model agentss
    :param parameters: object which holds all model parameters
    :return: list of agents
    """
    # 1 initialize low frequency traders
    low_frequency_traders = []
    total_lft = parameters["n_lft"]

    def divide_by_lfts(variable): return np.divide(variable, total_lft)

    for idx in range(total_lft):
        weight_fundamentalist = parameters['w_fundamentalists']
        weight_chartist = parameters['w_chartists']
        weight_random = parameters['w_random']
        lft_vars = Traderariables(parameters['wealth'], weight_fundamentalist, weight_chartist, weight_random)
        previous_lft_vars = Traderariables(parameters['wealth'], weight_fundamentalist, weight_chartist, weight_random)
        lft_params = TraderParameters(parameters['ma_short'], parameters['ma_long'])
        lft_expectations = TraderExpectations(parameters['init_price'])
        low_frequency_traders.append(LFTrader(idx, lft_vars, previous_lft_vars, lft_params, lft_expectations))

    return low_frequency_traders
