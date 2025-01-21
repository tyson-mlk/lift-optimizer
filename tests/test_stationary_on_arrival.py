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
async def passenger_arrival_event():
    await passenger_arrival('000', '003', datetime.now())
    await asyncio.sleep(10)
    await passenger_arrival('002', '000', datetime.now())

# simulates run of multiple continuous exponential processes in fixed time
@pytest.mark.asyncio
async def all_arrivals():
    jobs = [passenger_arrival_event()]
    start_time = datetime.now()
    print(f'test start: {start_time}')
    await asyncio.gather(*jobs)

@pytest.mark.asyncio
async def lift_operation():
    l1 = Lift('L1', '000', 'U')
    PASSENGERS.register_lift(l1)

    # need to let lifts take up only unassigned passengers
    await asyncio.gather(
        l1.lift_baseline_operation()
    )

@pytest.mark.asyncio
async def track():
    l1 = PASSENGERS.tracking_lifts[0]
    await asyncio.sleep(8)
    # test for stationary state when no targets are outstanding
    assert PASSENGERS.count_passengers() == 1
    assert (PASSENGERS.df.loc[1,['current', 'status', 'lift']].values == ['003', 'Arrived', 'L1']).all()
    assert l1.dir == 'S'
    await asyncio.sleep(6)
    assert (PASSENGERS.df.loc[2,[ 'status', 'lift']].values == ['Onboard', 'L1']).all()
    assert l1.dir == 'D'
    print('tests passed')

@pytest.mark.asyncio
async def main():
    timeout = 15
    try:
        async with asyncio.timeout(timeout):
            await asyncio.gather(all_arrivals(), lift_operation(), track())
    except asyncio.TimeoutError:
        pass

asyncio.run(main())
