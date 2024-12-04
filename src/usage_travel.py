# usage example
# start from src/ folder
import base
from datetime import datetime
import pandas as pd
import asyncio

p_list = base.PassengerList.PASSENGERS
p1 = base.Passenger.Passenger('000', '010', datetime.now())
p1_df = base.PassengerList.PassengerList.passenger_to_df(p1) 
p2 = base.Passenger.Passenger('000', '002', datetime.now())
p2_df = base.PassengerList.PassengerList.passenger_to_df(p2)
pp12 = base.PassengerList.PassengerList(pd.concat([p1_df, p2_df]))
p_list.passenger_list_arrival(pp12)
# p_list.passenger_arrival(base.Passenger.Passenger('000', '010', datetime.now()))
# p_list.passenger_arrival(base.Passenger.Passenger('000', '002', datetime.now()))
async def arrive_one_passenger():
    await p_list.passenger_arrival(base.Passenger.Passenger('010', '000', datetime.now()))

asyncio.run(arrive_one_passenger())

f_list = base.FloorList.FLOOR_LIST
ground = f_list.get_floor('000')
first = f_list.get_floor('001')
second = f_list.get_floor('002')
tenth = f_list.get_floor('010')

pa0 = ground.passengers
pa10 = tenth.passengers

l1 = base.Lift.Lift('l1', '000', 'U')

def print_status(prefix, lift):
    print(f"{prefix}. Lift {lift.name} at floor {lift.floor} with {lift.passengers.count_passengers()} passengers on-board")

async def main():
    print_status('A', l1) # Floor 0
    await l1.loading(print_lift_stats = True, print_passenger_stats=True)

    print_status('B', l1) # Floor 0

    lift_target = f_list.get_floor(l1.next_baseline_target())
    l1.manual_move(lift_target)

    p_list.passenger_arrival(base.Passenger.Passenger('004', '000', datetime.now()))
    p_list.passenger_arrival(base.Passenger.Passenger('008', '010', datetime.now()))

    await l1.loading(print_lift_stats = True, print_passenger_stats=True)

    print_status('C', l1) # Floor 2

    lift_target = f_list.get_floor(l1.next_baseline_target())
    l1.manual_move(lift_target)

    await l1.loading(print_lift_stats = True, print_passenger_stats=True)

    print_status('D',  l1) # Floor 8

    lift_target = f_list.get_floor(l1.next_baseline_target())
    l1.manual_move(lift_target)

    p_list.passenger_arrival(base.Passenger.Passenger('008', '011', datetime.now()))

    await l1.loading(print_lift_stats = True, print_passenger_stats=True)

    print_status('E',  l1) # Floor 10

    lift_target = f_list.get_floor(l1.next_baseline_target())
    l1.manual_move(lift_target)

    p_list.passenger_arrival(base.Passenger.Passenger('001', '005', datetime.now()))

    await l1.loading(print_lift_stats = True, print_passenger_stats=True)

    print_status('F',  l1) # Floor 4

    lift_target = f_list.get_floor(l1.next_baseline_target())
    l1.manual_move(lift_target)

    await l1.loading(print_lift_stats = True, print_passenger_stats=True)

    print_status('G',  l1) # Floor 0

    lift_target = f_list.get_floor(l1.next_baseline_target())
    l1.manual_move(lift_target)

    await l1.loading(print_lift_stats = True, print_passenger_stats=True)

    print_status('H',  l1) # Floor 1

    lift_target = f_list.get_floor(l1.next_baseline_target())
    l1.manual_move(lift_target)
    
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

# from metrics.MovingModel import MovingHeight

# mh = MovingHeight('000', '002')
# mh.print_status(*mh.calc_state(3))
