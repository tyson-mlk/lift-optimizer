# usage example
# start from src/ folder
import src.base
from datetime import datetime
import pandas as pd
import asyncio

import src.base.PassengerList

p_list = src.base.PassengerList.PASSENGERS
p1 = src.base.Passenger.Passenger('G', 'L10', datetime.now())
p1_df = src.base.PassengerList.PassengerList.passenger_to_df(p1) 
p2 = src.base.Passenger.Passenger('G', 'L02', datetime.now())
p2_df = src.base.PassengerList.PassengerList.passenger_to_df(p2)
pp12 = src.base.PassengerList.PassengerList(pd.concat([p1_df, p2_df]))
p_list.passenger_list_arrival(pp12)
# p_list.passenger_arrival(src.base.Passenger.Passenger('000', '010', datetime.now()))
# p_list.passenger_arrival(src.base.Passenger.Passenger('000', '002', datetime.now()))
async def arrive_one_passenger():
    await p_list.passenger_arrival(src.base.Passenger.Passenger('L10', 'G', datetime.now()))

asyncio.run(arrive_one_passenger())

f_list = src.base.FloorList.FLOOR_LIST
ground = f_list.get_floor('G')
first = f_list.get_floor('L01')
second = f_list.get_floor('L02')
tenth = f_list.get_floor('L10')

pa0 = ground.passengers
pa10 = tenth.passengers

l1 = src.base.Lift.Lift('l1', 'G', 'S')
p_list.register_lift(l1)
# l2 = src.base.Lift.Lift('l2', '000', 'S')
# p_list.register_lift(l2)
# l3 = src.base.Lift.Lift('l3', '005', 'S')
# p_list.register_lift(l3)

def print_status(prefix, lift):
    print(f"{prefix}. Lift {lift.name} at floor {lift.floor} facing {lift.dir} with {lift.passengers.count_passengers()} passengers on-board")

async def main():
    print_status('A', l1) # Floor 0

    # to specify this time only for loading
    l1.next_dir = l1.dir
    await l1.loading(print_lift_stats = True, print_passenger_stats=True)

    print_status('B', l1) # Floor 0

    lift_target = l1.next_baseline_target()
    l1.update_next_dir(lift_target)
    await l1.move(f_list.get_floor(lift_target))
    
    p3 = src.base.Passenger.Passenger('L04', 'G', datetime.now())
    p3_df = src.base.PassengerList.PassengerList.passenger_to_df(p3) 
    p4 = src.base.Passenger.Passenger('L08', 'L10', datetime.now())
    p4_df = src.base.PassengerList.PassengerList.passenger_to_df(p4)
    pp34 = src.base.PassengerList.PassengerList(pd.concat([p3_df, p4_df]))
    p_list.passenger_list_arrival(pp34)

    await l1.loading(print_lift_stats = True, print_passenger_stats=True)

    print_status('C', l1) # Floor 2

    lift_target = l1.next_baseline_target()
    l1.update_next_dir(lift_target)
    await l1.move(f_list.get_floor(lift_target))

    await l1.loading(print_lift_stats = True, print_passenger_stats=True)

    print_status('D',  l1) # Floor 8

    lift_target = l1.next_baseline_target()
    print('lift target', lift_target)
    l1.update_next_dir(lift_target)
    print('lift next dir', l1.next_dir)
    await l1.move(f_list.get_floor(lift_target))

    p5 = src.base.Passenger.Passenger('L08', 'L11', datetime.now())
    p5_df = src.base.PassengerList.PassengerList.passenger_to_df(p5)
    p_list.passenger_list_arrival(src.base.PassengerList.PassengerList(passenger_list_df = p5_df))

    await l1.loading(print_lift_stats = True, print_passenger_stats=True)

    print_status('E',  l1) # Floor 10

    lift_target = l1.next_baseline_target()
    l1.update_next_dir(lift_target)
    await l1.move(f_list.get_floor(lift_target))

    p6 = src.base.Passenger.Passenger('L01', 'L05', datetime.now())
    p6_df = src.base.PassengerList.PassengerList.passenger_to_df(p6)
    p_list.passenger_list_arrival(src.base.PassengerList.PassengerList(passenger_list_df = p6_df))

    await l1.loading(print_lift_stats = True, print_passenger_stats=True)

    print_status('F',  l1) # Floor 4

    lift_target = l1.next_baseline_target()
    l1.update_next_dir(lift_target)
    await l1.move(f_list.get_floor(lift_target))

    await l1.loading(print_lift_stats = True, print_passenger_stats=True)

    print_status('G',  l1) # Floor 0

    lift_target = l1.next_baseline_target()
    l1.update_next_dir(lift_target)
    await l1.move(f_list.get_floor(lift_target))

    await l1.loading(print_lift_stats = True, print_passenger_stats=True)

    print_status('H',  l1) # Floor 1

    lift_target = l1.next_baseline_target()
    l1.update_next_dir(lift_target)
    await l1.move(f_list.get_floor(lift_target))
    
    await l1.loading(print_lift_stats = True, print_passenger_stats=True)

    print_status('I',  l1) # Floor 5

asyncio.run(main())

# p_list.df
# l1.passengers.df

# ground.random_select_passengers(1,0)

# l1.has_floor_capacity()
# l1.capacity = 1
# l1.onboard_random_available()

# l1.onboard_all()

# l1.move(first)

# l1.offboard_selected()

# from src.base.metrics.MovingModel import MovingHeight

# mh = MovingHeight('000', '002')
# mh.print_status(*mh.calc_state(3))
