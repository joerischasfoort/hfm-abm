"""Simulation file used to run the model"""

from init_objects import *
from hft_model import *

# 1 setup parameters
parameters = {
    # global parameters
    "n_lft": 50,
    "n_hft": 5,
    "ticks": 1000,
    "fundamental_value": 10,
    "lft_sample_size": 0.2,
    "hft_sample_size": 0.6,
    "std_noise": 0.01,
    "std_LFT_price": 0.01,
    "std_LFT_vol": 4,
    "std_HFT_vol": 4,
    "return_on_investment": 0.5,
    "investment_frequency": 100,
    # lft parameters
    "w_fundamentalists": 1,
    "w_chartists": 10,
    "w_random": 1,
    # hft parameters
    "inventory_target": 20,
    "minimum_price_increment":0.1,
    "investment_fraction":0.4,
    "$hfm_risk_aversion": 10,
    # initial values
    "wealth": 300,
    "horizon_min": 1,
    "horizon_max": 4,
    "av_return_interval_max": 4,
    "init_price": 1,
    "agent_order_price_variability": (1,1),
    "total_hft_money": 200,
    "hft_speed": 1,
    "hft_init_investment": 0
}

# 2 initalise model objects
high_frequency_traders, low_frequency_traders, orderbook = init_objects(parameters)

# 3 simulate model
high_frequency_traders, low_frequency_traders, orderbook = hft_model(high_frequency_traders, low_frequency_traders, orderbook, parameters, seed=1)