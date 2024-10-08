import asyncio
from random import expovariate
from datetime import datetime

FLOORS = list(str(i).zfill(3) for i in range(1, 5))
FLOOR_HEIGHTS = {'001': 0, '002': 5, '003': 8, '004': 11}
TRIPS = [
    (source, target, 'U' if target > source else 'D')
    for source in FLOORS for target in FLOORS if source != target
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

# simulates exponential arrival time of passengers
async def exp_gen(rate=1.0):
    start_time = datetime.now()
    # print('task taking ', mean, 'started')
    time_taken = expovariate(rate)
    await asyncio.sleep(time_taken)
    end_time = datetime.now()
    # print('task taking ', mean, 'ended taking', end_time-start_time)

# simulates continuous arrival
async def cont_exp_gen(rate=1.0, trip):
    try:
        while True:
            await exp_gen(rate=rate)
            increment_counter(counter_type=trip)
    except MemoryError:
        print('memory error')
        return None

# simulates run of 3 continuous exponential processes in fixed time
async def main():
    jobs = [cont_exp_gen(rate=l) for l in [1, 1/3, 1/5]]
    timeout = 20
    print('all start')
    try:
        start_time = datetime.now()
        async with asyncio.timeout(timeout):
            await asyncio.gather(*jobs)
            # print('completed after', datetime.now()-start_time, 'seconds')
    except asyncio.TimeoutError:
        print(f'timeout after {timeout} seconds')
        print('counter', COUNTERS)

if __name__ == "__main__":
    asyncio.run(main=main())
