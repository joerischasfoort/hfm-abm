"""Simulation file used to run the model"""

from init_objects import *
from hft_model import *

# 1 setup parameters
parameters = {
    # global parameters
    "n_lft": 100,
    "n_hft": 1,
    "ticks": 1000, # 390 ticks per day
    "ticks_per_minute": 1,
    "fundamental_value": 10,
    "std_fundamental": 0.0,
    "lft_sample_size": 0.03,
    "hft_sample_size": 1.0,
    "std_noise": 0.01,
    "std_LFT_vol": 1,
    "std_HFT_vol": 4,
    "max_order_expiration_ticks": 30,
    "transaction_fee": 0.0,
    "max_spread_exchange": 0.01,
    # lft parameters
    "w_fundamentalists": 1.0, #1
    "w_chartists": 0.0, # 10
    "w_random": 4.0,
    "spread_max": 0.004087, # from Riordann & Storkenmaier 2012
    # hft parameters
    "inventory_target": 10,
    "minimum_price_increment": 0.001,
    "hfm_risk_aversion": 0.01,
    "hfm_adaptive_param": 0.2,
    "hfm_volatility_sensitivity": 1.9,
    # initial values
    "horizon_min": 1,
    "horizon_max": 9,
    "hfm_horizon_min": 1,
    "hfm_horizon_max": 5,
    "total_hft_money": 250,
    "hft_speed": 1,
}

# 2 initalise model objects
high_frequency_traders, low_frequency_traders, orderbook = init_objects(parameters, seed=1)

# 3 simulate model
high_frequency_traders, low_frequency_traders, orderbook = hft_model(high_frequency_traders, low_frequency_traders, orderbook, parameters, seed=1)