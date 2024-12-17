import asyncio
from datetime import datetime
from base.Passenger import Passenger
from base.PassengerList import PASSENGERS
from base.Lift import Lift

async def passenger_arrival(source_floor, target_floor, start_time):
    new_passenger = Passenger(source_floor, target_floor, start_time)
    await PASSENGERS.passenger_arrival(new_passenger)

async def job_start():
    await passenger_arrival('000', '005', datetime.now())
    print('job_start passenger arrived', datetime.now())
    await asyncio.sleep(0)

async def job_reload():
    await asyncio.sleep(0.2)
    await passenger_arrival('002', '003', datetime.now())
    print('job_reload passenger arrived', datetime.now())
    await asyncio.sleep(0)

# simulates run of multiple continuous exponential processes in fixed time
async def all_arrivals():
    jobs = [job_start(), job_reload()]
    start_time = datetime.now()
    print(f'all start: {start_time}')
    await asyncio.gather(*jobs)
    
async def lift_operation():
    l1 = Lift('L1', '000', 'U')
    PASSENGERS.register_lift(l1)

    # need to let lifts take up only unassigned passengers
    await asyncio.gather(
        l1.lift_baseline_operation()
    )

async def track():
    await asyncio.sleep(0)
    # first passenger arrived
    assert PASSENGERS.count_passengers() == 1
    l1 = PASSENGERS.tracking_lifts[0]
    await asyncio.sleep(0.1)
    # passenger assigned lift l1 at 0.1 s
    assert l1.loading_state['current_target'] == '005'
    await asyncio.sleep(0.2)
    # second passenger arrived
    assert PASSENGERS.count_passengers() == 2
    # lift reassigned to floor 002 at 0.3 s
    assert l1.loading_state['current_target'] == '002'
    await asyncio.sleep(6.2)
    # lift arrived to floor 002 at 6.5 s
    assert l1.floor == '002'

async def main():
    timeout = 7
    start_time = datetime.now()
    start_time.hour
    try:
        async with asyncio.timeout(timeout):
            await asyncio.gather(all_arrivals(), lift_operation(), track())
    except asyncio.TimeoutError:
        pass

asyncio.run(main())
print('tests passed')
