import numpy as np


def div0(a, b):
    """
    ignore / 0, and return 0 div0( [-1, 0, 1], 0 ) -> [0, 0, 0]
    credits to Dennis @ https://stackoverflow.com/questions/26248654/numpy-return-0-with-divide-by-zero
    """
    answer = np.true_divide(a, b)
    if not np.isfinite(answer):
        answer = 0
    return answer