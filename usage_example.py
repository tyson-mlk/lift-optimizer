# usage example
# start from src/ folder
import base
from datetime import datetime

p_list = base.PassengerList.PASSENGERS
p_list.passenger_arrival(base.Passenger.Passenger('000', '010', datetime.now()))
p_list.passenger_arrival(base.Passenger.Passenger('000', '002', datetime.now()))
p_list.passenger_arrival(base.Passenger.Passenger('010', '000', datetime.now()))

f_list = base.FloorList.FLOOR_LIST
ground = f_list.get_floor('000')
first = f_list.get_floor('001')
second = f_list.get_floor('002')
tenth = f_list.get_floor('010')

pa0 = ground.passengers
pa10 = tenth.passengers

l1 = base.Lift.Lift('l1', '000', 'U')

print('A', l1.floor, l1.passengers.df) # Floor 0

l1.offboard_arrived()
l1.onboard_random_available()

print('B', l1.floor, l1.passengers.df) # Floor 0

lift_target = f_list.get_floor(l1.next_baseline_target())
l1.move(lift_target)

l1.offboard_arrived()
l1.onboard_random_available()

p_list.passenger_arrival(base.Passenger.Passenger('004', '000', datetime.now()))
p_list.passenger_arrival(base.Passenger.Passenger('008', '010', datetime.now()))

print('C', l1.floor, l1.passengers.df) # Floor 2

lift_target = f_list.get_floor(l1.next_baseline_target())
l1.move(lift_target)

l1.offboard_arrived()
l1.onboard_random_available()

print('D',  l1.floor, l1.passengers.df) # Floor 8

lift_target = f_list.get_floor(l1.next_baseline_target())
l1.move(lift_target)

l1.offboard_arrived()
l1.onboard_random_available()

p_list.passenger_arrival(base.Passenger.Passenger('008', '011', datetime.now()))

print('E',  l1.floor, l1.passengers.df) # Floor 10

lift_target = f_list.get_floor(l1.next_baseline_target())
l1.move(lift_target)

l1.offboard_arrived()
l1.onboard_random_available()

p_list.passenger_arrival(base.Passenger.Passenger('001', '005', datetime.now()))

print('F',  l1.floor, l1.passengers.df) # Floor 4

lift_target = f_list.get_floor(l1.next_baseline_target())
l1.move(lift_target)

l1.offboard_arrived()
l1.onboard_random_available()

print('G',  l1.floor, l1.passengers.df) # Floor 0

lift_target = f_list.get_floor(l1.next_baseline_target())
l1.move(lift_target)

l1.offboard_arrived()
l1.onboard_random_available()

print('H',  l1.floor, l1.passengers.df) # Floor 1

lift_target = f_list.get_floor(l1.next_baseline_target())
l1.move(lift_target)

l1.offboard_arrived()
l1.onboard_random_available()

print('I',  l1.floor, l1.passengers.df) # Floor 5

p_list.update_passenger_metrics()
print(p_list.df)

# p_list.df
# l1.passengers.df

# ground.random_select_passengers(1,0)

# l1.has_capacity()
# l1.capacity = 1
# l1.onboard_random_available()

# l1.onboard_all()

# l1.move(first)

# l1.offboard_selected()
