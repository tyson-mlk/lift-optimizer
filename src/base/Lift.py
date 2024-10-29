import asyncio

from base.Floor import Floor
from base.PassengerList import PassengerList, PASSENGERS
from base.FloorList import FLOOR_LIST, MAX_FLOOR, MIN_FLOOR, FLOOR_HEIGHTS
from metrics.MovingTime import MovingTime
# from Passenger import Passenger

LIFT_CAPACITY_DEFAULT = 12

class Lift:
    "lift class"

    def __init__(self, name, floor, dir, capacity = LIFT_CAPACITY_DEFAULT, model = "accel") -> None:
        self.name = name
        self.floor = floor
        self.dir = dir
        self.capacity = capacity
        self.passenger_count = 0
        self.passengers: PassengerList = PassengerList()
        self.calculate_passenger_count()

    def calculate_passenger_count(self) -> None:
        self.passenger_count = self.passengers.count_passengers()

    def get_current_floor(self) -> Floor:
        return FLOOR_LIST.get_floor(self.floor)

    def get_current_floor_passengers(self):
        return self.get_current_floor().passengers

    def get_current_floor_passenger_count(self) -> int:
        return self.get_current_floor().get_floor_count()

    def has_capacity(self):
        floor_count = self.get_current_floor().get_floor_count()
        return self.passenger_count + floor_count <= self.capacity

    def onboard_all(self):
        floor = self.get_current_floor()
        PASSENGERS.assign_lift_for_floor(self, floor)
        self.passengers.bulk_add_passengers(floor.passengers)
        self.passengers.assign_lift(self)
        floor.onboard_all()
        self.calculate_passenger_count()

    def onboard_random_selection(self, floor: Floor):
        if self.has_capacity():
            selection = floor.passengers.df
        else:
            selection = floor.random_select_passengers(self.capacity, self.passenger_count)
        passenger_list = PassengerList(selection)
        PASSENGERS.assign_lift_for_selection(self, passenger_list)
        floor.onboard_selected(passenger_list)
        self.passengers.bulk_add_passengers(passenger_list)
        self.passengers.assign_lift(self)
        self.calculate_passenger_count()

    def onboard_earliest_arrival(self, floor: Floor):
        if self.has_capacity():
            selection = floor.passengers.df
        else:
            selection = floor.select_passengers_by_earliest_arrival(self.capacity, self.passenger_count)
        passenger_list = PassengerList(selection)
        PASSENGERS.assign_lift_for_selection(self, passenger_list)
        floor.onboard_selected(passenger_list)
        self.passengers.bulk_add_passengers(passenger_list)
        self.passengers.assign_lift(self)
        self.calculate_passenger_count()

    def offboard_all(self):
        # TODO: to log arrival times of passengers
        PASSENGERS.update_arrival(self.passengers)
        self.passengers.remove_all_passengers()
        self.calculate_passenger_count()

    def offboard_arrived(self):
        # TODO: to log arrival times of passengers
        current_floor = FLOOR_LIST.get_floor(self.floor)
        to_offboard = self.passengers.filter_by_destination(current_floor)
        self.passengers.remove_passengers(to_offboard)
        self.calculate_passenger_count()
        PASSENGERS.update_arrival(to_offboard)

    # to init test
    def offboard(self, passengers: PassengerList):
        # TODO: to log arrival times of passengers
        self.passengers.remove_passengers(passengers)
        self.calculate_passenger_count()
        PASSENGERS.update_arrival(passengers)
        
    # async def move(self, floor):
    #     "moves to floor, assumes it is on a stopped state"
    #     current_floor = FLOOR_LIST.get_floor(self.floor)
    #     time_to_move = self.calc_time_to_move(current_floor, floor)
    #     print('time to move is', time_to_move)
    #     if floor.floor > self.floor:
    #         self.dir = 'U'
    #     elif floor.floor < self.floor:
    #         self.dir = 'D'
    #     else:
    #         self.dir = 'S'

    #     await asyncio.sleep(time_to_move)

    #     if floor.floor == MIN_FLOOR:
    #         self.dir = 'U'
    #     elif floor.floor == MAX_FLOOR:
    #         self.dir = 'D'
        
    #     self.floor = floor.floor
    #     self.passengers.update_passenger_floor(floor)
    #     PASSENGERS.update_lift_passenger_floor(self, floor)

        
    def move(self, floor):
        "moves to floor, assumes it is on a stopped state"
        current_floor = FLOOR_LIST.get_floor(self.floor)
        time_to_move = self.calc_time_to_move(current_floor, floor)
        print('time to move is', time_to_move)
        if floor.floor > self.floor:
            self.dir = 'U'
        elif floor.floor < self.floor:
            self.dir = 'D'
        else:
            self.dir = 'S'

        import time
        time.sleep(time_to_move)

        if floor.floor == MIN_FLOOR:
            self.dir = 'U'
        elif floor.floor == MAX_FLOOR:
            self.dir = 'D'
        
        self.floor = floor.floor
        self.passengers.update_passenger_floor(floor)
        PASSENGERS.update_lift_passenger_floor(self, floor)


    def calc_time_to_move(self, old_floor, new_floor):
        "distance lookup function takes into account time for acceleration and deceleration"
        from metrics.MovingTime import MovingTime

        new_height = new_floor.height
        old_height = old_floor.height
        distance = abs( new_height - old_height)
        return MovingTime().calc_model(distance)
    
    def next_lift_passenger_target(self):
        passenger_targets = self.passengers.passenger_request_scan()
        if passenger_targets.shape[0] == 0:
            return None
        if self.dir == 'U':
            floor_scan = passenger_targets.loc[
                (passenger_targets.source_floor > self.floor) &
                (passenger_targets.dir == 'U'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.min()
            floor_scan = passenger_targets.loc[
                (passenger_targets.dir == 'D'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.max()
            return passenger_targets.source_floor.min()
        elif self.dir == 'D':
            floor_scan = passenger_targets.loc[
                (passenger_targets.source_floor < self.floor) &
                (passenger_targets.dir == 'D'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.min()
            floor_scan = passenger_targets.loc[
                (passenger_targets.dir == 'U'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.min()
            return passenger_targets.source_floor.max()
    
    def next_overall_target_baseline(self):
        target = PassengerList()
        target.bulk_add_passengers(self.passengers)
        target.bulk_add_passengers(PASSENGERS)
        overall_targets = target.passenger_request_scan()
        if overall_targets.shape[0] == 0:
            return None
        if self.dir == 'U':
            floor_scan = overall_targets.loc[
                (overall_targets.source_floor > self.floor) &
                (overall_targets.dir == 'U'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.min()
            floor_scan = overall_targets.loc[
                (overall_targets.dir == 'D'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.max()
            return overall_targets.source_floor.min()
        elif self.dir == 'D':
            floor_scan = overall_targets.loc[
                (overall_targets.source_floor < self.floor) &
                (overall_targets.dir == 'D'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.min()
            floor_scan = overall_targets.loc[
                (overall_targets.dir == 'U'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.min()
            return overall_targets.source_floor.max()


    # TODO: move function to main control    
    # def stop(self, floor):
    #     self.alight(floor)
    #     eligible_floors = master.get_eligible_floors(floor)
    #     master.get_floor_passengers(floor).board(eligible_floors, self)
