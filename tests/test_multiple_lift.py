import asyncio
from datetime import datetime
from base.Passenger import Passenger
from base.PassengerList import PASSENGERS
from base.Lift import Lift

async def passenger_arrival(source_floor, target_floor, start_time):
    new_passenger = Passenger(source_floor, target_floor, start_time)
    await PASSENGERS.passenger_arrival(new_passenger)

async def job_arrival():
    await passenger_arrival('001', '002', datetime.now())
    print('first passenger arrival', datetime.now())
    await asyncio.sleep(1)
    await passenger_arrival('002', '003', datetime.now())
    print('second passenger arrival', datetime.now())
    await passenger_arrival('001', '003', datetime.now())
    print('third passenger arrival', datetime.now())
    await asyncio.sleep(9)
    await passenger_arrival('003', '001', datetime.now())
    await passenger_arrival('005', '006', datetime.now())
    await asyncio.sleep(4)
    await passenger_arrival('001', '000', datetime.now())
    await asyncio.sleep(5)
    await passenger_arrival('005', '006', datetime.now())


# simulates run of multiple continuous exponential processes in fixed time
async def all_arrivals():
    jobs = [job_arrival()]
    start_time = datetime.now()
    print(f'all start: {start_time}')
    await asyncio.gather(*jobs)
    
async def lift_operation():
    l1 = Lift('L1', '000', 'U')
    PASSENGERS.register_lift(l1)
    l2 = Lift('L2', '000', 'U')
    PASSENGERS.register_lift(l2)

    # need to let lifts take up only unassigned passengers
    await asyncio.gather(
        l1.lift_baseline_operation(),
        l2.lift_baseline_operation(),
    )

async def track():
    await asyncio.sleep(0)
    l2 = PASSENGERS.tracking_lifts[1]
    await asyncio.sleep(1.2)
    # test that passengers are assigned relating to pre-existing assignments
    assert (PASSENGERS.df.loc[[1,2,3],'lift'].values == ['L1', 'L2', 'L1']).all()
    await asyncio.sleep(11)
    assert PASSENGERS.df.loc[5,'lift'] == 'L2'
    await asyncio.sleep(2)
    # test for lift turning when all further passengers are assigned
    assert PASSENGERS.df.loc[4,'lift'] == 'L1'
    await asyncio.sleep(12)
    # test for passenger 7 served by L2 after L1 served all remaining
    assert 7 in l2.passengers.df.index
    

async def main():
    timeout = 27
    start_time = datetime.now()
    start_time.hour
    try:
        async with asyncio.timeout(timeout):
            await asyncio.gather(all_arrivals(), lift_operation(), track())
    except asyncio.TimeoutError:
        pass

asyncio.run(main())
print('tests passed')
