import asyncio
from datetime import datetime
from base.Passenger import Passenger
from base.PassengerList import PASSENGERS
from base.Lift import Lift

async def passenger_arrival(source_floor, target_floor, start_time):
    new_passenger = Passenger(source_floor, target_floor, start_time)
    await PASSENGERS.passenger_arrival(new_passenger)

async def passenger_arrival_event():
    await passenger_arrival('000', '001', datetime.now())
    await passenger_arrival('000', '001', datetime.now())
    await passenger_arrival('000', '001', datetime.now())
    await asyncio.sleep(0)

# simulates run of multiple continuous exponential processes in fixed time
async def all_arrivals():
    jobs = [passenger_arrival_event()]
    start_time = datetime.now()
    print(f'test start: {start_time}')
    await asyncio.gather(*jobs)
    
async def lift_operation():
    l1 = Lift('L1', '000', 'U')
    l1.capacity = 2
    PASSENGERS.register_lift(l1)

    # need to let lifts take up only unassigned passengers
    await asyncio.gather(
        l1.lift_baseline_operation()
    )

async def track():
    await asyncio.sleep(0.1)
    l1 = PASSENGERS.tracking_lifts[0]
    # test for initial state for passenger count
    assert PASSENGERS.count_passengers() == 3
    await asyncio.sleep(2)
    # test for passenger lift assigned and boarded
    assert PASSENGERS.filter_by_status_waiting().count_passengers() == 1
    assert PASSENGERS.filter_by_lift_assigned(l1).count_passengers() == 2
    assert l1.passengers.count_passengers() == 2

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
