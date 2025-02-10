import asyncio
from datetime import datetime
from src.base.Passenger import Passenger
from src.base.PassengerList import PASSENGERS
from src.base.Lift import Lift

async def passenger_arrival(source_floor, target_floor, start_time):
    new_passenger = Passenger(source_floor, target_floor, start_time)
    await PASSENGERS.passenger_arrival(new_passenger)

async def passenger_arrives_event():
    await passenger_arrival('000', '001', datetime.now())
    await asyncio.sleep(0)

# simulates run of multiple continuous exponential processes in fixed time
async def all_arrivals():
    jobs = [passenger_arrives_event()]
    start_time = datetime.now()
    print(f'test start: {start_time}')
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
    l1 = PASSENGERS.tracking_lifts[0]
    # test for initial state after passenger arrival
    assert (PASSENGERS.df.loc[1,['current', 'status', 'lift']].values == ['000', 'Waiting', 'Unassigned']).all()
    assert l1.passengers.count_passengers() == 0
    await asyncio.sleep(0.2)
    # test for passenger lift assigned after 0.2 s
    assert (PASSENGERS.df.loc[1,['current', 'status', 'lift']].values == ['000', 'Onboard', 'L1']).all()
    assert l1.passengers.count_passengers() == 1
    await asyncio.sleep(5.8)
    # test for destination arrived after 6 s
    assert (PASSENGERS.df.loc[1,['current', 'status', 'lift']].values == ['001', 'Arrived', 'L1']).all()
    assert l1.passengers.count_passengers() == 0

async def main():
    timeout = 10
    start_time = datetime.now()
    start_time.hour
    try:
        async with asyncio.timeout(timeout):
            await asyncio.gather(all_arrivals(), lift_operation(), track())
    except asyncio.TimeoutError:
        pass

asyncio.run(main())
print('tests passed')
