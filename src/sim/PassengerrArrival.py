import asyncio
from base.Floor import Floor
from random import expovariate
from datetime import datetime

FLOORS = list(Floor(str(i).zfill(3)) for i in range(1, 5))
FLOOR_HEIGHTS = {'001': 0, '002': 5, '003': 8, '004': 11}
TRIPS = [(
    source.floor(), target.floor(),
    'U' if target.floor() > source.floor() else 'D'
    )   for source in FLOORS for target in FLOORS if source != target
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

class Trip:
    def __init__(self, source_floor, target_floor) -> None:
        self.source_floor = source_floor
        self.target_floor = target_floor
        if self.target_floor > self.source_floor:
            self.direction = 'U'
        elif self.source_floor > self.target_floor:
            self.direction = 'D'
        
    @property
    def source_floor(self):
        return self._source_floor
    
    @property
    def target_floor(self):
        return self._target_floor
    
    @property
    def direction(self):
        return self._direction


def increment_counter(counter_type):
    COUNTERS[counter_type] += 1

# untested
def passenger_arrival(source_floor, target_floor):
    floor = filter(lambda x: x.floor() == source_floor, FLOORS)
    floor.passenger_arrival(target_floor)

# simulates exponential arrival time of passengers
async def exp_gen(rate=1.0):
    time_taken = expovariate(rate)
    await asyncio.sleep(time_taken)

# simulates continuous arrival
async def cont_exp_gen(trip, rate=1.0):
    try:
        while True:
            start_time = datetime.now()
            await exp_gen(rate=rate)
            increment_counter(counter_type=trip)
            end_time = datetime.now()
            # for logging
            # print('trip', trip, 'rate ', rate, 'generated taking', end_time-start_time)
    except MemoryError:
        print('memory error')
        return None

# simulates run of 3 continuous exponential processes in fixed time
async def main():
    jobs = [cont_exp_gen(trip=k, rate=v) for k,v in trip_arrival_rates.items()]
    timeout = 20
    print('all start')
    try:
        start_time = datetime.now()
        async with asyncio.timeout(timeout):
            await asyncio.gather(*jobs)
    except asyncio.TimeoutError:
        print(f'timeout after {timeout} seconds')
        print('counter', COUNTERS)

if __name__ == "__main__":
    asyncio.run(main=main())
