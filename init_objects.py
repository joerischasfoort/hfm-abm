import numpy as np
from objects.trader import *
from objects.orderbook import *

def init_objects(parameters):
    """
    Function to initialise the model agentss
    :param parameters: object which holds all model parameters
    :return: list of agents
    """
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
        lft_vars = Tradervariables(parameters['wealth'], 0, weight_fundamentalist, weight_chartist, weight_random)
        previous_lft_vars = Tradervariables(parameters['wealth'], 0, weight_fundamentalist, weight_chartist, weight_random)
        lft_params = TraderParameters(parameters['horizon_min'], parameters['horizon_max'])
        lft_expectations = TraderExpectations(parameters['init_price'])
        low_frequency_traders.append(LFTrader(idx, lft_vars, previous_lft_vars, lft_params, lft_expectations))

    for idx in range(total_hft):
        hft_vars = HFTvariables(divide_by_agents(parameters["total_hft_money"], total_hft),
                                parameters["inventory_target"],
                                parameters["hft_speed"] + parameters["hft_init_investment"]**parameters["return_on_investment"],
                                parameters["hft_init_investment"])
        previous_hft_vars = HFTvariables(divide_by_agents(parameters["total_hft_money"], total_hft),
                                         parameters["inventory_target"],
                                         parameters["hft_speed"] + parameters["hft_init_investment"] ** parameters["return_on_investment"],
                                         parameters["hft_init_investment"])
        hft_params = HFTParameters(parameters["inventory_target"], parameters["minimum_price_increment"], parameters["investment_fraction"])
        high_frequency_traders.append(HFTrader(idx, hft_vars, previous_hft_vars, hft_params))

    orderbook = LimitOrderBook(parameters['fundamental_value'], parameters["agent_order_price_variability"], parameters['horizon_max'])

    return high_frequency_traders, low_frequency_traders, orderbook
