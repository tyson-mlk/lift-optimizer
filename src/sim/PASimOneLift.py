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
            trip_arrival_rates[key] = 0.05
        else:
            trip_arrival_rates[key] = 0.01

# define lift
l1 = Lift('l1', '000', 'U')

def increment_counter(counter_type):
    COUNTERS[counter_type] += 1

def passenger_arrival(source_floor, target_floor, start_time):
    new_passenger = Passenger(source_floor, target_floor, start_time)
    PASSENGERS.passenger_arrival(new_passenger)

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
            start_time = datetime.now()
            await exp_gen(rate=rate)
            passenger_arrival(source_floor, target_floor, datetime.now())
            end_time = datetime.now()
            # for logging
            print('trip', trip, 'rate ', rate, 'generated taking', end_time-start_time)
    except MemoryError:
        print('memory error')
        return None

# simulates run of multiple continuous exponential processes in fixed time
async def all_arrivals():
    jobs = [cont_exp_gen(trip=k, rate=v) for k,v in trip_arrival_rates.items()]
    start_time = datetime.now()
    print(f'all start: {start_time}')
    await asyncio.gather(*jobs)

# PASSENGERS.passenger_arrival(Passenger('004', '000', datetime.now()))
# PASSENGERS.passenger_arrival(Passenger('008', '010', datetime.now()))


async def main():
    timeout = 20
    try:
        async with asyncio.timeout(timeout):
            await asyncio.gather(all_arrivals(), l1.lift_baseline_operation())
    except asyncio.TimeoutError:
        print('timeout')

if __name__ == "__main__":
    # TODO: nothing is run with main()
    asyncio.run(main())
