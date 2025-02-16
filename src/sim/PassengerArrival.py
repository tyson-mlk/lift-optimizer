import asyncio
from random import expovariate
from datetime import datetime
from src.base.Floor import Floor
from src.base.FloorList import FloorList
from src.base.Passenger import Passenger
from src.base.PassengerList import PASSENGERS

FLOORS = list(str(i).zfill(3) for i in range(1, 5))
FLOOR_HEIGHTS = {'001': 0, '002': 5, '003': 8, '004': 11}
FLOOR_LIST = FloorList(FLOORS, FLOOR_HEIGHTS)
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
trip_arrival_rates = {
    ('001', '002', 'U'): 1,
    ('001', '003', 'U'): 0.5,
    ('001', '004', 'U'): 0.5,
    ('002', '001', 'D'): 0.75,
    ('002', '003', 'U'): 0.375,
    ('002', '004', 'U'): 0.625,
    ('003', '001', 'D'): 0.125,
    ('003', '002', 'D'): 0.625,
    ('003', '004', 'U'): 0.125,
    ('004', '001', 'D'): 0.125,
    ('004', '002', 'D'): 0.625,
    ('004', '003', 'D'): 0.25,
}

# class Trip:
#     def __init__(self, source_floor, target_floor) -> None:
#         self.source_floor = source_floor
#         self.target_floor = target_floor
#         if self.target_floor > self.source_floor:
#             self.direction = 'U'
#         elif self.source_floor > self.target_floor:
#             self.direction = 'D'
        
#     @property
#     def source_floor(self):
#         return self._source_floor
    
#     @property
#     def target_floor(self):
#         return self._target_floor
    
#     @property
#     def direction(self):
#         return self._direction


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
            increment_counter(trip)
            end_time = datetime.now()
            # for logging
            print('trip', trip, 'rate ', rate, 'generated taking', end_time-start_time)
    except MemoryError:
        print('memory error')
        return None

# simulates run of 3 continuous exponential processes in fixed time
async def main():
    jobs = [cont_exp_gen(trip=k, rate=v) for k,v in trip_arrival_rates.items()]
    timeout = 5
    start_time = datetime.now()
    print(f'all start: {start_time}')
    try:
        async with asyncio.timeout(timeout):
            await asyncio.gather(*jobs)
    except asyncio.TimeoutError:
        print(f'timeout after {timeout} seconds')
        print('counter', COUNTERS)
        print('arrived passengers: ', PASSENGERS.df)

if __name__ == "__main__":
    asyncio.run(main=main())
