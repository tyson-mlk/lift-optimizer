import asyncio
from random import expovariate
from datetime import datetime

COUNTERS = {1:0, 3:0, 5:0}

def increment_counter(counter_type):
    COUNTERS[counter_type] += 1

# simulates exponential arrival time of passengers
async def exp_gen(mean=1.0):
    start_time = datetime.now()
    # print('task taking ', mean, 'started')
    time_taken = expovariate(1/mean)
    await asyncio.sleep(time_taken)
    end_time = datetime.now()
    # print('task taking ', mean, 'ended taking', end_time-start_time)

# simulates continuous arrival
async def cont_exp_gen(mean=1.0):
    try:
        while True:
            await exp_gen(mean=mean)
            increment_counter(counter_type=mean)
    except MemoryError:
        print('memoery error')
        return None

# simulates run of 3 continuous exponential processes in fixed time
async def main():
    jobs = [cont_exp_gen(mean=l) for l in [1, 3, 5]]
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
