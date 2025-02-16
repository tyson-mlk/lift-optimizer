import asyncio
from random import expovariate
from datetime import datetime
from src.base.FloorList import FLOOR_LIST
from src.base.Passenger import Passenger
from src.base.PassengerList import PASSENGERS
from src.base.Lift import Lift

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
            trip_arrival_rates[key] = 0.003
        else:
            trip_arrival_rates[key] = 0.0002

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
    start_time = datetime.now()
    print(f'all start: {start_time}')
    await asyncio.gather(*jobs)
    
async def lift_operation():
    l1 = Lift('l1', '000', 'U')
    PASSENGERS.register_lift(l1)

    task = asyncio.create_task(l1.lift_baseline_operation())
    await task

async def main():
    timeout = 500
    start_time = datetime.now()
    start_time.hour
    try:
        async with asyncio.timeout(timeout):
            await asyncio.gather(all_arrivals(), lift_operation())
    except asyncio.TimeoutError:
        print('timeout: save passengers to file')
        time_start_str = f'{start_time.hour:02}_{start_time.minute:02}_{start_time.second:02}'
        out_file = f'../data/PASimOneLift_{time_start_str}.csv'
        PASSENGERS.df.sort_values(['status', 'dir', 'source', 'trip_start_time']) \
            .to_csv(out_file)
