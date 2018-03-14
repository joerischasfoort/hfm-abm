""""The main model"""
import numpy as np
import random

def hft_model(low_frequency_traders, parameters, seed=1):
    """The main model function"""
    random.seed(seed)
    np.random.seed(seed)

    for day in range(parameters["ticks"]):
        active_traders = random.sample(low_frequency_traders, int((parameters['lft_sample_size'] * len(low_frequency_traders))))

        for trader in active_traders:
            # update expectations
            print(trader)
            # submit orders

        # orderbook.match_orders

    return low_frequency_traders