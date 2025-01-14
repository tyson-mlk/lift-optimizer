"""
Simulation of multiple lifts moving with baseline coordination setting
In a tower of 20 floors, 5 lifts and 
passengers arrival rates from a statistical Poisson process
After running through 1 hour, passenger records are saved to file
"""

import asyncio
from random import expovariate
from datetime import datetime
from base.FloorList import FLOOR_LIST
from base.Passenger import Passenger
from base.PassengerList import PASSENGERS
from base.Lift import Lift

TRIPS = [(
    source, target,
    'U' if target > source else 'D'
    )
    for source in FLOOR_LIST.list_floors()
    for target in FLOOR_LIST.list_floors()
    if source != target
]
COUNTERS = {t:0 for t in TRIPS}

# for simulation
trip_arrival_rates = {}
for source in FLOOR_LIST.list_floors():
    for target in FLOOR_LIST.list_floors():
        if target == source:
            continue
        elif target > source:
            dir = 'U'
        else:
            dir = 'D'
        key = (source, target, dir)
        if (source == '000') | (target == '000'):
            trip_arrival_rates[key] = 0.00005 # sparse request
            # trip_arrival_rates[key] = 0.003 # one lift busy
            # trip_arrival_rates[key] = 0.006 # two lifts busy
            # trip_arrival_rates[key] = 0.012 # five lifts busy
        else:
            trip_arrival_rates[key] = 0.00005 # sparse request
            # trip_arrival_rates[key] = 0.0002 # one lift busy
            # trip_arrival_rates[key] = 0.0004 # two lifts busy
            # trip_arrival_rates[key] = 0.001 # five lifts busy

def increment_counter(counter_type):
    COUNTERS[counter_type] += 1

async def passenger_arrival(source_floor, target_floor, start_time):
    new_passenger = Passenger(source_floor, target_floor, start_time)
    await PASSENGERS.passenger_arrival(new_passenger)

# simulates exponential arrival time of passengers
async def exp_gen(rate=1.0):
    time_taken = expovariate(rate)
    await asyncio.sleep(time_taken)

# simulates continuous arrival
async def cont_exp_gen(trip, rate=1.0):
    try:
        source_floor = trip[0]
        target_floor = trip[1]
        while True:
            await exp_gen(rate=rate)
            await passenger_arrival(source_floor, target_floor, datetime.now())
            # for debugging
            # print('passenger arrived from', trip[0], 'moving', trip[2], 'to', trip[1])
            await asyncio.sleep(0)
    except MemoryError:
        print('memory error')
        return None

# simulates run of multiple continuous exponential processes in fixed time
async def all_arrivals():
    jobs = [cont_exp_gen(trip=k, rate=v) for k,v in trip_arrival_rates.items()]
    jobs += [PASSENGERS.reassignment_listener()]
    start_time = datetime.now()
    print(f'all start: {start_time}')
    arrival_timeout = 1680
    try:
        async with asyncio.timeout(arrival_timeout):
            await asyncio.gather(*jobs)
    except asyncio.TimeoutError:
        print('PASSENGERS ARRIVAL COMPLETE')
        PASSENGERS.log('PASSENGERS ARRIVAL COMPLETE')
    
async def lift_operation():
    l1 = Lift('L1', '000', 'U')
    PASSENGERS.register_lift(l1)
    l2 = Lift('L2', '000', 'U')
    PASSENGERS.register_lift(l2)
    l3 = Lift('L3', '000', 'U')
    PASSENGERS.register_lift(l3)
    l4 = Lift('L4', '000', 'U')
    PASSENGERS.register_lift(l4)
    l5 = Lift('L5', '000', 'U')
    PASSENGERS.register_lift(l5)
    # l6 = Lift('L6', '000', 'U')
    # PASSENGERS.register_lift(l6)
    # l7 = Lift('L7', '000', 'U')
    # PASSENGERS.register_lift(l7)
    # l8 = Lift('L8', '000', 'U')
    # PASSENGERS.register_lift(l8)

    # need to let lifts take up only unassigned passengers
    await asyncio.gather(
        l1.lift_baseline_operation(),
        l2.lift_baseline_operation(),
        l3.lift_baseline_operation(),
        l4.lift_baseline_operation(),
        l5.lift_baseline_operation(),
        # l6.lift_baseline_operation(),
        # l7.lift_baseline_operation(),
        # l8.lift_baseline_operation()
    )

async def main():
    timeout = 1800
    start_time = datetime.now()
    start_time.hour
    try:
        async with asyncio.timeout(timeout):
            await asyncio.gather(all_arrivals(), lift_operation())
    except asyncio.TimeoutError:
        print('timeout: save passengers to file')
        time_start_str = f'{start_time.hour:02}_{start_time.minute:02}_{start_time.second:02}'
        out_file = f'../data/PAMultLift_{time_start_str}.csv'
        PASSENGERS.df.sort_values(['status', 'dir', 'source', 'trip_start_time']) \
            .to_csv(out_file)
