import numpy as np
def mLogScale(m, max):
    return int(np.e**((m/128.0)*np.log(max)) - 1)