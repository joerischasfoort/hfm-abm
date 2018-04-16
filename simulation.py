"""Simulation file used to run the model"""

from init_objects import *
from hft_model import *

# 1 setup parameters
parameters = {
    # global parameters
    "n_lft": 50,
    "n_hft": 1,
    "ticks": 1000,
    "fundamental_value": 1000,
    "lft_sample_size": 0.2,
    "hft_sample_size": 1.0,
    "std_noise": 0.01,
    "std_LFT_price": 0.01,
    "std_LFT_vol": 4,
    # lft parameters
    "w_fundamentalists": 0.4,
    "w_chartists": 0.4,
    "w_random": 0.2,
    # hft parameters
    "inventory_target": 20,
    "minimum_price_increment":0.1,
    # initial values
    "wealth": 300,
    "horizon_min": 1,
    "horizon_max": 4,
    "av_return_interval_max": 4,
    "init_price": 1,
    "agent_order_price_variability": (1,1),
    "total_hft_money": 100,
    "total_hft_inventory": 0
}

# 2 initalise model objects
high_frequency_traders, low_frequency_traders, orderbook = init_objects(parameters)

# 3 simulate model
high_frequency_traders, low_frequency_traders, orderbook = hft_model(high_frequency_traders, low_frequency_traders, orderbook, parameters, seed=1)