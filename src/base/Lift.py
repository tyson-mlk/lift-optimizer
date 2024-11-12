import asyncio
import pandas as pd

from base.Floor import Floor
from base.PassengerList import PassengerList, PASSENGERS
from base.FloorList import FLOOR_LIST, MAX_FLOOR, MIN_FLOOR
from metrics.MovingModel import MovingModel, MovingStatus

LIFT_CAPACITY_DEFAULT = 12

class Lift:
    "lift class"

    def __init__(self, name, floorname, dir, capacity = LIFT_CAPACITY_DEFAULT, model = "accel") -> None:
        self.name = name
        self.floor = floorname
        self.height = self.get_current_floor().height
        self.dir = dir
        self.capacity = capacity
        self.passenger_count = 0
        self.passengers: PassengerList = PassengerList()
        self.calculate_passenger_count()
        self.model = MovingModel(model=model)

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
        PASSENGERS.board(PASSENGERS.filter_by_floor(floor))

        import time
        from metrics.BoardingTime import boarding_time

        num_to_onboard = floor.passengers.count_passengers()
        time_to_onboard = boarding_time(self, self.passenger_count, 0, num_to_onboard)
        if time_to_onboard > 0:
            print(f'onboarding {num_to_onboard} passengers takes {time_to_onboard} s')
            time.sleep(time_to_onboard)

        self.passengers.bulk_add_passengers(floor.passengers)
        self.passengers.assign_lift(self)
        self.passengers.board(floor.passengers)
        floor.onboard_all()
        self.calculate_passenger_count()

    def onboard_random_available(self):
        floor = FLOOR_LIST.get_floor(self.floor)
        if self.has_capacity():
            selection = floor.passengers.df
        else:
            selection = floor.random_select_passengers(self.capacity, self.passenger_count)
        passenger_list = PassengerList(selection)

        import time
        from metrics.BoardingTime import boarding_time

        num_to_onboard = passenger_list.count_passengers()
        time_to_onboard = boarding_time(self, self.passenger_count, 0, num_to_onboard)
        if time_to_onboard > 0:
            print(f'onboarding {num_to_onboard} passengers takes {time_to_onboard} s')
            time.sleep(time_to_onboard)

        PASSENGERS.assign_lift_for_selection(self, passenger_list)
        PASSENGERS.board(passenger_list)
        floor.onboard_selected(passenger_list)
        self.passengers.bulk_add_passengers(passenger_list)
        self.passengers.assign_lift(self)
        self.passengers.board(passenger_list)
        self.calculate_passenger_count()

    def onboard_earliest_arrival(self):
        floor = FLOOR_LIST.get_floor(self.floor)
        if self.has_capacity():
            selection = floor.passengers.df
        else:
            selection = floor.select_passengers_by_earliest_arrival(self.capacity, self.passenger_count)
        passenger_list = PassengerList(selection)

        import time
        from metrics.BoardingTime import boarding_time

        num_to_onboard = passenger_list.count_passengers()
        time_to_onboard = boarding_time(self, self.passenger_count, 0, num_to_onboard)
        if time_to_onboard > 0:
            print(f'onboarding {num_to_onboard} passengers takes {time_to_onboard} s')
            time.sleep(time_to_onboard)

        PASSENGERS.assign_lift_for_selection(self, passenger_list)
        PASSENGERS.board(passenger_list)
        floor.onboard_selected(passenger_list)
        self.passengers.bulk_add_passengers(passenger_list)
        self.passengers.assign_lift(self)
        self.passengers.board(passenger_list)
        self.calculate_passenger_count()

    def offboard_all(self):
        # TODO: to log arrival times of passengers
        PASSENGERS.update_arrival(self.passengers)

        import time
        from metrics.BoardingTime import boarding_time

        num_to_offboard = self.passenger_count
        time_to_offboard = boarding_time(self, num_to_offboard, num_to_offboard, 0)
        if time_to_offboard > 0:
            print(f'offboarding {num_to_offboard} passengers takes {time_to_offboard} s')
            time.sleep(time_to_offboard)

        self.passengers.remove_all_passengers()
        self.calculate_passenger_count()

    def offboard_arrived(self):
        # TODO: to log arrival times of passengers
        current_floor = FLOOR_LIST.get_floor(self.floor)
        to_offboard = self.passengers.filter_by_destination(current_floor)

        import time
        from metrics.BoardingTime import boarding_time

        num_to_offboard = to_offboard.count_passengers()
        time_to_offboard = boarding_time(self, self.passenger_count, num_to_offboard, 0)
        if time_to_offboard > 0:
            print(f'offboarding {num_to_offboard} passengers takes {time_to_offboard} s')
            time.sleep(time_to_offboard)

        self.passengers.remove_passengers(to_offboard)
        self.calculate_passenger_count()
        PASSENGERS.update_arrival(to_offboard)

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
        if floor.height > self.height:
            self.dir = 'U'
        elif floor.height < self.height:
            self.dir = 'D'
        else:
            self.dir = 'S'

        import time
        time.sleep(time_to_move)

        if floor.name == MIN_FLOOR:
            self.dir = 'U'
        elif floor.name == MAX_FLOOR:
            self.dir = 'D'
        
        self.floor = floor.name
        self.height = floor.height
        self.passengers.update_passenger_floor(floor)
        PASSENGERS.update_lift_passenger_floor(self, floor)


    def calc_time_to_move(self, old_floor, new_floor):
        "distance lookup function takes into account time for acceleration and deceleration"

        new_height = new_floor.height
        old_height = old_floor.height
        distance = abs( new_height - old_height)
        return self.model.calc_time(distance)

    # to init test
    def calc_time_to_move_while_moving(self, time_elapsed, new_floor):
        moving_status = MovingStatus(
            source=self.get_current_floor().name,
            target=new_floor.name,
            a=self.model.a, max_v=self.model.max_v, model=self.model.model_type
        )
        height, direction, velocity = moving_status.calc_state(time_elapsed)
        new_floor_height = FLOOR_LIST.get_floor(new_floor).height
        return moving_status.calc_time(height, direction, velocity, new_floor_height)

    def next_lift_passenger_target(self):
        """
        next lift target by passengers in the lift
        this is a minimum constraint for lift service contract
        """
        passenger_targets = self.passengers.passenger_target_scan().rename(
            columns={'target': 'lift_target'}
        )
        return self.find_next_lift_target(passenger_targets)
    
    def next_baseline_target(self):
        """
        baseline for lift target algorithm
        attends to the most immediate request
        """
        lift_targets = self.passengers.passenger_target_scan().rename(
            columns={'target': 'lift_target'}
        )
        passengers_in_wait = PassengerList(PASSENGERS.df.loc[PASSENGERS.df.lift == 'Unassigned', :])
        waiting_targets = passengers_in_wait.passenger_source_scan().rename(
            columns={'source': 'lift_target'}
        )
        overall_targets = pd.concat([lift_targets, waiting_targets])
        return self.find_next_lift_target(overall_targets)
        
    def find_next_lift_target(self, targets):
        if targets.shape[0] == 0:
            return None
        if self.dir == 'U':
            floor_scan = targets.loc[
                (targets.lift_target > self.floor) &
                (targets.dir == 'U'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.lift_target.min()

            floor_scan = targets.loc[
                (targets.dir == 'D'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.lift_target.max()

            return targets.lift_target.min()
        elif self.dir == 'D':
            floor_scan = targets.loc[
                (targets.lift_target < self.floor) &
                (targets.dir == 'D'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.lift_target.min()

            floor_scan = targets.loc[
                (targets.dir == 'U'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.lift_target.min()

            return targets.lift_target.max()
