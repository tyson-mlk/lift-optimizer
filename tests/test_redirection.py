import asyncio
import pytest
from datetime import datetime
from base.Passenger import Passenger
from base.PassengerList import PASSENGERS
from base.Lift import Lift

@pytest.mark.asyncio
async def passenger_arrival(source_floor, target_floor, start_time):
    new_passenger = Passenger(source_floor, target_floor, start_time)
    await PASSENGERS.passenger_arrival(new_passenger)

@pytest.mark.asyncio
async def job_start():
    await passenger_arrival('000', '005', datetime.now())
    print('job_start passenger arrived', datetime.now())
    await asyncio.sleep(0)

@pytest.mark.asyncio
async def job_reload():
    await asyncio.sleep(1)
    await passenger_arrival('002', '003', datetime.now())
    print('job_reload passenger arrived', datetime.now())
    await asyncio.sleep(0)

# simulates run of multiple continuous exponential processes in fixed time
@pytest.mark.asyncio
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

@pytest.mark.asyncio
async def track():
    await asyncio.sleep(0)
    # first passenger arrived
    assert PASSENGERS.count_passengers() == 1
    l1 = PASSENGERS.tracking_lifts[0]
    await asyncio.sleep(0.7)
    # passenger assigned lift l1 at 0.7 s
    assert l1.floor_move_state['target_floor'] == '005'
    await asyncio.sleep(0.8)
    # second passenger arrived
    assert PASSENGERS.count_passengers() == 2
    # lift redirected to floor 002 at 1.5 s
    assert l1.redirect_state['target_floor'] == '002'
    await asyncio.sleep(5)
    # lift arrived to floor 002 at 6.5 s
    assert l1.floor == '002'

@pytest.mark.asyncio
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
