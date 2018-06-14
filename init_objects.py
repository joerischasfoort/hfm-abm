import numpy as np
from objects.trader import *
from objects.orderbook import *


def init_objects(parameters, seed=1):
    """
    Function to initialise the model agentss
    :param parameters: object which holds all model parameters
    :return: list of agents
    """
    np.random.seed(seed)

    # 1 initialize low frequency traders
    low_frequency_traders = []
    high_frequency_traders = []
    total_lft = parameters["n_lft"]
    total_hft = parameters["n_hft"]

    def divide_by_agents(variable, agents): return np.divide(variable, agents)

    for idx in range(total_lft):
        weight_fundamentalist = parameters['w_fundamentalists']
        weight_chartist = parameters['w_chartists']
        weight_random = parameters['w_random']
        lft_vars = Tradervariables(0, 0, weight_fundamentalist, weight_chartist, weight_random)
        lft_params = TraderParameters(parameters['horizon_min'], parameters['horizon_max'], parameters['spread_max'])
        lft_expectations = TraderExpectations(parameters['fundamental_value'])
        low_frequency_traders.append(LFTrader(idx, lft_vars, lft_params, lft_expectations))

    for idx in range(total_hft):
        hft_vars = HFTvariables(divide_by_agents(parameters["total_hft_money"], total_hft),
                                parameters["inventory_target"],
                                parameters["hft_speed"],
                                divide_by_agents(parameters["total_hft_money"], total_hft) + parameters["inventory_target"] * parameters["fundamental_value"],
                                {'price': 0, 'age': 0})
        previous_hft_vars = HFTHistory(divide_by_agents(parameters["total_hft_money"], total_hft),
                                       parameters["inventory_target"],
                                       parameters["hft_speed"],
                                       divide_by_agents(parameters["total_hft_money"], total_hft) + parameters[
                                           "inventory_target"] * parameters["fundamental_value"],
                                       parameters["spread_max"])
        hft_params = HFTParameters(parameters["inventory_target"], parameters["minimum_price_increment"],
                                   parameters["hfm_horizon_min"], parameters["hfm_horizon_max"],
                                   parameters["hfm_risk_aversion"], parameters["hfm_adaptive_param"])
        high_frequency_traders.append(HFTrader(idx, hft_vars, previous_hft_vars, hft_params))

    orderbook = LimitOrderBook(parameters['fundamental_value'], parameters["spread_max"],
                               parameters['horizon_max'], parameters['max_order_expiration_ticks'])

    return high_frequency_traders, low_frequency_traders, orderbook
