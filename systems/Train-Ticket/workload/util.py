from scipy import interpolate
import numpy as np
import json


with open('/mnt/locust/config.json') as f:
    CFG = json.load(f)

TIME_LIMIT = CFG['TimeLimit']


def load_userconfig(HttpUser):
    classname = HttpUser.__name__
    users = CFG[classname]['users']
    peaks = CFG[classname]['peaks']
    return users, peaks

def create_next_usercount(HttpUser, scipy=False):
    users, peaks = load_userconfig(HttpUser)
    num_segments = 12
    y = np.array([users]*num_segments)
    for pos, peak_users in peaks:
        y[round(num_segments*pos)] = peak_users
    x = np.linspace(0, TIME_LIMIT, len(y)).astype(int)
    
    f = interpolate.interp1d(x, y, kind='quadratic')
    return f if scipy else lambda t: round(float(f(t)))

def tick(fun, usercount, runtime):
    if runtime < TIME_LIMIT:
        next_usercount = fun(runtime)
        if next_usercount > usercount:
            spawn_rate =  next_usercount - usercount
        else:
            spawn_rate = 1       
        return (next_usercount, spawn_rate)

    return None

