#!/usr/bin/env python
# coding: utf-8

import random
import json
import sys
from math import ceil

DELAYS_CONFIG_JSON = "latency-injector/src/main/resources/delays.json"
NOISES_CONFIG_JSON = "latency-injector/src/main/resources/noises.json"
SYNC_RPCS_PATH = "syncRPCs.txt"
ASYNC_RPCS_PATH = "asyncRPCs.txt"

NUM_AFFECTED_CLASSES = 2
NUM_REQ_CLASSES = 10
NOISE_PROB = 0.5
MAX_AFFECTED_RPCS_WCLASS = 3

## Request avg during a 5min load test without injection
## load test params: (--c) 20 users (--r) 1 hatch rate (--run-time)  5 minutes 
## user waiting time: wait_time = between(1.0, 3.0) random waiting time between 1 seconds and 3 seconds
REQ_AVG = 116


def create_delays(rpcs):
    delay_rpc_kind = random.uniform(REQ_AVG*0.2, REQ_AVG*0.4) /len(rpcs)
    num_calls =[int(rpc.split(',')[2]) for rpc in rpcs]
    return [int(ceil(delay_rpc_kind/n)) for n in num_calls]


def read_rpcs(RPCS_PATH):
    with open(RPCS_PATH, mode='r') as f:
        rpcs = [url.replace('\n', '') for url in f.readlines()]
    return rpcs


def random_rpcs(rpcs):
    return sorted(random.sample(rpcs, k=random.randint(1, MAX_AFFECTED_RPCS_WCLASS)))


def select_affected_syncrpcs(rpcs):
    affected_rpcs = []
    while len(affected_rpcs) < NUM_AFFECTED_CLASSES:
        selected_rpcs = random_rpcs(rpcs)
        if selected_rpcs not in affected_rpcs:
            affected_rpcs.append(selected_rpcs)
    return affected_rpcs

def select_affected_asyncrpc(rpcs):
    return random.choice(rpcs)



def create_delays_cfg(affected_rpcs):
    cfg = []

    for rpcs  in affected_rpcs:
        pattern = []
        delays = create_delays(rpcs)
        for rpc, delay in zip(rpcs, delays):
            method, uri, _ = rpc.split(',')
            pattern.append({"uri": uri, "method":method, "delay": delay})
        cfg.append(pattern)
    return cfg


def create_noises_cfg(affected_rpc):
    cfg = []
    delay = int(ceil(random.uniform(REQ_AVG*0.2, REQ_AVG*0.4)))
    method, uri, _ = affected_rpc.split(',')
    cfg.append({'uri': uri, 'method': method, 'prob': NOISE_PROB, 'delay': delay})
    return cfg

def write_configs(delays_cfg, noises_cfg):
    with open(DELAYS_CONFIG_JSON, mode='w') as f:
        json.dump(delays_cfg, f, indent=3)

    with open(NOISES_CONFIG_JSON, mode='w') as f:
        json.dump(noises_cfg, f, indent=3)


def main():
    syncrpcs = read_rpcs(SYNC_RPCS_PATH)
    asyncrpcs = read_rpcs(ASYNC_RPCS_PATH)
    affected_syncrpcs = select_affected_syncrpcs(syncrpcs)
    affected_asyncrpc = select_affected_asyncrpc(asyncrpcs)
    delays_cfg = create_delays_cfg(affected_syncrpcs)
    noises_cfg = create_noises_cfg(affected_asyncrpc)
    write_configs(delays_cfg, noises_cfg)


if __name__ == "__main__":
    main()
