import asyncio
from datetime import datetime
from base.Passenger import Passenger
from base.PassengerList import PASSENGERS
from base.Lift import Lift

async def passenger_arrival(source_floor, target_floor, start_time):
    new_passenger = Passenger(source_floor, target_floor, start_time)
    await PASSENGERS.passenger_arrival(new_passenger)

async def job_arrival():
    await passenger_arrival('000', '002', datetime.now())
    await passenger_arrival('003', '005', datetime.now())
    print('job_start passenger arrived', datetime.now())
    # make sure lift has fetched passenger 2 by time 12 s
    await passenger_arrival('004', '003', datetime.now())
    await passenger_arrival('002', '001', datetime.now())
    await asyncio.sleep(12)
    await passenger_arrival('000', '001', datetime.now())

# simulates run of multiple continuous exponential processes in fixed time
async def all_arrivals():
    jobs = [job_arrival()]
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
    await asyncio.sleep(0.1)
    # first 2 passenger arrived
    assert PASSENGERS.count_passengers() == 4
    l1 = PASSENGERS.tracking_lifts[0]
    await asyncio.sleep(7.3)
    # passenger 1 has reached by time 7.4 s
    assert PASSENGERS.df.loc[1,'status'] == 'Arrived'
    await asyncio.sleep(4.5)
    # lift has moved with passenger 2 by time 11.9 s
    assert (
        l1.floor_move_state['start_move_floor'] == '003' and 
        l1.floor_move_state['target_floor'] == '005'
    )
    # lift has moved downards to fetch passenger by time 17.4
    await asyncio.sleep(5.5)
    assert (l1.dir == 'D' and l1.next_dir == 'D')
    # passenger 3 has reached by time 25.4
    await asyncio.sleep(8)
    assert PASSENGERS.df.loc[3,'status'] == 'Arrived'
    # passenger 4 has reached by time 33.4
    await asyncio.sleep(8)
    assert PASSENGERS.df.loc[4,'status'] == 'Arrived'
    assert PASSENGERS.count_passengers() == 5
    assert (l1.dir == 'D' and l1.next_dir == 'U')
    await asyncio.sleep(5)
    assert l1.dir == 'U'
    print('U-turn test passed')

async def main():
    timeout = 39
    start_time = datetime.now()
    start_time.hour
    try:
        async with asyncio.timeout(timeout):
            await asyncio.gather(all_arrivals(), lift_operation(), track())
    except asyncio.TimeoutError:
        pass

asyncio.run(main())
print('tests passed')
