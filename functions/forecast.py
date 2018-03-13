import numpy as np
from functions.helpers import *


def forecast_return(price, fundamental_price, average_return, std_noise, weight_fundamental, weight_chartist, weight_random):
    """
    Equation traders forecast return using a weighted combination between fundamentalist, chartists and random factors
    :param price: float last price of the asset
    :param fundamental_price: float price which the agent beliefs to be the fundamental price
    :param average_return: float average previous return
    :param std_noise: float standard deviation of the noise process
    :param weight_fundamental: float weight of the fundamental factor
    :param weight_chartist: float weight of the chartist factor
    :param weight_random: float weight of the random factor
    :return: float expected return of the asset
    """
    noise = np.random.normal(0, std_noise)
    expected_return = weight_fundamental * div0(fundamental_price - price, price) + weight_chartist * average_return + weight_random * noise
    return expected_return


def forecast_price(current_price, expected_return):
    """
    Equation low frequency trader forecasts price based on its expected return and current price
    :param current_price:
    :param expected_return:
    :return:
    """
    expected_price = current_price * np.exp(expected_return)
    return expected_price


def draw_weights(std_f, std_c, std_n):
    """
    Draw weights from a random normal distribution with standard devations
    :param std_f: float standard deviation of fundamentalists
    :param std_c: float standard deviation of chartists
    :param std_n: float standard deviation of random traders
    :return: np array of weights
    """
    # draw weights from a random normal distribution
    sigmas = [std_f, std_c, std_n]
    weights = np.array([np.random.normal(1, sigma) for sigma in sigmas])

    # normalize weights
    row_sums = weights.sum()
    new_matrix = weights / row_sums
    return new_matrix