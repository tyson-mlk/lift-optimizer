# usage example
# start from src/ folder
import base

p_list = base.PassengerList.PASSENGERS
p_list.passenger_arrival(base.Passenger.Passenger('000', '010'))
p_list.passenger_arrival(base.Passenger.Passenger('000', '002'))
p_list.passenger_arrival(base.Passenger.Passenger('010', '000'))

ground = base.FloorList.FLOOR_LIST.get_floor('000')
first = base.FloorList.FLOOR_LIST.get_floor('001')
second = base.FloorList.FLOOR_LIST.get_floor('002')
tenth = base.FloorList.FLOOR_LIST.get_floor('010')

pa0 = ground.passengers
pa10 = tenth.passengers

l1 = base.Lift.Lift('l1', '000', 'U')

ground.random_select_passengers(1,0)

l1.has_capacity()
l1.capacity = 1
l1.onboard_random_selection(ground)

l1.onboard_all()

l1.move(first)

l1.offboard_selected()
