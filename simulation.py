"""Simulation file used to run the model"""

from init_objects import *
from hft_model import *

# 1 setup parameters
parameters = {
    # global parameters
    "n_lft": 10,
    "n_hft": 1,
    "ticks": 10,
    "lft_sample_size": 0.2,
    # agent parameters
    "w_fundamentalists": 0.4,
    "w_chartists": 0.4,
    "w_random": 0.2,
    # initial values
    "wealth": 300,
    "ma_short": 1,
    "ma_long": 4,
    "init_price": 1,
}

# 2 initalise model objects
low_frequency_traders = init_objects(parameters)

# 3 simulate model
low_frequency_traders = hft_model(low_frequency_traders, parameters, seed=1)