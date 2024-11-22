# usage example
# start from src/ folder
import base
from datetime import datetime
import pandas as pd

p_list = base.PassengerList.PASSENGERS
p1 = base.Passenger.Passenger('000', '010', datetime.now())
p1_df = base.PassengerList.PassengerList.passenger_to_df(p1) 
p2 = base.Passenger.Passenger('000', '002', datetime.now())
p2_df = base.PassengerList.PassengerList.passenger_to_df(p2)
pp12 = base.PassengerList.PassengerList(pd.concat([p1_df, p2_df]))
p_list.passenger_list_arrival(pp12)
# p_list.passenger_arrival(base.Passenger.Passenger('000', '010', datetime.now()))
# p_list.passenger_arrival(base.Passenger.Passenger('000', '002', datetime.now()))
p_list.passenger_arrival(base.Passenger.Passenger('010', '000', datetime.now()))

f_list = base.FloorList.FLOOR_LIST
ground = f_list.get_floor('000')
first = f_list.get_floor('001')
second = f_list.get_floor('002')
tenth = f_list.get_floor('010')

pa0 = ground.passengers
pa10 = tenth.passengers

l1 = base.Lift.Lift('l1', '000', 'U')

print('A', l1.name, l1.passengers.df, p_list.df) # Floor 0

l1.offboard_arrived()
# l1.onboard_random_available()
l1.onboard_earliest_arrival()

p_list.update_passenger_metrics()

# to use async
# await l1.loading()

print('B', l1.name, l1.passengers.df, p_list.df) # Floor 0

lift_target = f_list.get_floor(l1.next_baseline_target())
l1.move(lift_target)

l1.offboard_arrived()
# l1.onboard_random_available()
l1.onboard_earliest_arrival()

p_list.passenger_arrival(base.Passenger.Passenger('004', '000', datetime.now()))
p_list.passenger_arrival(base.Passenger.Passenger('008', '010', datetime.now()))

p_list.update_passenger_metrics()

print('C', l1.name, l1.passengers.df, p_list.df) # Floor 2

lift_target = f_list.get_floor(l1.next_baseline_target())
l1.move(lift_target)

l1.offboard_arrived()
# l1.onboard_random_available()
l1.onboard_earliest_arrival()

p_list.update_passenger_metrics()

print('D',  l1.name, l1.passengers.df, p_list.df) # Floor 8

lift_target = f_list.get_floor(l1.next_baseline_target())
l1.move(lift_target)

l1.offboard_arrived()
# l1.onboard_random_available()
l1.onboard_earliest_arrival()

p_list.passenger_arrival(base.Passenger.Passenger('008', '011', datetime.now()))

p_list.update_passenger_metrics()

print('E',  l1.name, l1.passengers.df, p_list.df) # Floor 10

lift_target = f_list.get_floor(l1.next_baseline_target())
l1.move(lift_target)

l1.offboard_arrived()
# l1.onboard_random_available()
l1.onboard_earliest_arrival()

p_list.passenger_arrival(base.Passenger.Passenger('001', '005', datetime.now()))

p_list.update_passenger_metrics()

print('F',  l1.name, l1.passengers.df, p_list.df) # Floor 4

lift_target = f_list.get_floor(l1.next_baseline_target())
l1.move(lift_target)

l1.offboard_arrived()
# l1.onboard_random_available()
l1.onboard_earliest_arrival()

p_list.update_passenger_metrics()

print('G',  l1.name, l1.passengers.df, p_list.df) # Floor 0

lift_target = f_list.get_floor(l1.next_baseline_target())
l1.move(lift_target)

l1.offboard_arrived()
# l1.onboard_random_available()
l1.onboard_earliest_arrival()

p_list.update_passenger_metrics()

print('H',  l1.name, l1.passengers.df, p_list.df) # Floor 1

lift_target = f_list.get_floor(l1.next_baseline_target())
l1.move(lift_target)

l1.offboard_arrived()
# l1.onboard_random_available()
l1.onboard_earliest_arrival()

p_list.update_passenger_metrics()

print('I',  l1.name, l1.passengers.df, p_list.df) # Floor 5

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
