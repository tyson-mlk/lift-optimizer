import asyncio
import pandas as pd
from datetime import datetime, timedelta
from logging import INFO, DEBUG

from utils.Logging import get_logger
from base.Floor import Floor
from base.PassengerList import PassengerList, PASSENGERS
from base.FloorList import FLOOR_LIST, MAX_FLOOR, MIN_FLOOR
from metrics.LiftSpec import LiftSpec
from metrics.CalcMovingFloor import CalcMovingFloor

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
        self.model = LiftSpec(model=model)
        logger = get_logger(name, self.__class__.__name__, INFO)
        detail_logger = get_logger(name+'_det', self.__class__.__name__, DEBUG)
        self.log = lambda msg: logger.info(msg)
        self.detail_log = lambda msg: detail_logger.debug(msg)
        self.log(f"{self.name}: init")

    def __del__(self):
        self.log(f"{self.name}: destruct")

    def calculate_passenger_count(self) -> None:
        self.passenger_count = self.passengers.count_passengers()

    def get_current_floor(self) -> Floor:
        return FLOOR_LIST.get_floor(self.floor)

    def get_current_floor_passengers(self):
        return self.get_current_floor().passengers

    def get_current_floor_passenger_count(self) -> int:
        return self.get_current_floor().get_floor_count()
    
    def has_capacity(self):
        return self.passenger_count < self.capacity

    def has_floor_capacity(self):
        floor_count = self.get_current_floor().get_floor_count()
        return self.passenger_count + floor_count <= self.capacity

    def onboard_all(self):
        floor = self.get_current_floor()
        PASSENGERS.assign_lift_for_floor(self, floor)
        PASSENGERS.board(PASSENGERS.filter_by_floor(floor))

        import time
        from metrics.BoardingTime import boarding_time

        num_to_onboard = floor.passengers.count_passengers()
        if num_to_onboard == 0:
            return None
        time_to_onboard = boarding_time(self, self.passenger_count, 0, num_to_onboard)
        if time_to_onboard > 0:
            self.detail_log(f'onboarding {num_to_onboard} passengers takes {time_to_onboard} s')
            time.sleep(time_to_onboard)

        self.log(
            f"{self.name}: "
            f"Onboarding {num_to_onboard} passengers "
            f"at floor {floor.name}"
        )
        self.passengers.bulk_add_passengers(floor.passengers)
        self.passengers.assign_lift(self)
        self.passengers.board(floor.passengers)
        floor.onboard_all()
        floor.log(
            f"{floor.name}: "
            f"{num_to_onboard} passengers boarded"
        )
        floor.log(
            f"{floor.name}:"
            f"passenger count is {floor.passengers.count_passengers()}"
        )
        self.calculate_passenger_count()
        self.log(
            f"{self.name}: "
            f"Updated passenger count {self.passenger_count} "
        )

    def onboard_random_available(self):
        floor = FLOOR_LIST.get_floor(self.floor)
        if self.has_floor_capacity():
            selection = floor.passengers.df
        else:
            selection = floor.random_select_passengers(self.capacity, self.passenger_count)
        passenger_list = PassengerList(selection)

        import time
        from metrics.BoardingTime import boarding_time

        num_to_onboard = passenger_list.count_passengers()
        if num_to_onboard == 0:
            return None
        time_to_onboard = boarding_time(self, self.passenger_count, 0, num_to_onboard)
        if time_to_onboard > 0:
            self.detail_log(f'onboarding {num_to_onboard} passengers takes {time_to_onboard} s')
            time.sleep(time_to_onboard)

        self.log(
            f"{self.name}: "
            f"Onboarding {num_to_onboard} passengers "
            f"at floor {floor.name}"
        )
        PASSENGERS.assign_lift_for_selection(self, passenger_list)
        PASSENGERS.board(passenger_list)
        floor.onboard_selected(passenger_list)
        floor.log(
            f"{floor.name}: "
            f"{num_to_onboard} passengers boarded"
        )
        floor.log(
            f"{floor.name}:"
            f"passenger count is {floor.passengers.count_passengers()}"
        )
        self.passengers.bulk_add_passengers(passenger_list)
        self.passengers.assign_lift(self)
        self.passengers.board(passenger_list)
        self.calculate_passenger_count()
        self.log(
            f"{self.name}: "
            f"Updated passenger count {self.passenger_count} "
        )

    def onboard_earliest_arrival(self):
        floor = FLOOR_LIST.get_floor(self.floor)
        if self.has_floor_capacity():
            selection = floor.passengers.df
        else:
            selection = floor.select_passengers_by_earliest_arrival(self.capacity, self.passenger_count)
        passenger_list = PassengerList(selection)

        import time
        from metrics.BoardingTime import boarding_time

        num_to_onboard = passenger_list.count_passengers()
        if num_to_onboard == 0:
            return None
        time_to_onboard = boarding_time(self, self.passenger_count, 0, num_to_onboard)
        if time_to_onboard > 0:
            self.detail_log(f'onboarding {num_to_onboard} passengers takes {time_to_onboard} s')
            time.sleep(time_to_onboard)

        self.log(
            f"{self.name}: "
            f"Onboarding {num_to_onboard} passengers "
            f"at floor {floor.name}"
        )
        PASSENGERS.assign_lift_for_selection(self, passenger_list)
        PASSENGERS.board(passenger_list)
        floor.onboard_selected(passenger_list)
        floor.log(
            f"{floor.name}: "
            f"{num_to_onboard} passengers boarded"
        )
        floor.log(
            f"{floor.name}:"
            f"passenger count is {floor.passengers.count_passengers()}"
        )
        self.passengers.bulk_add_passengers(passenger_list)
        self.passengers.assign_lift(self)
        self.passengers.board(passenger_list)
        self.calculate_passenger_count()
        self.log(
            f"{self.name}: "
            f"Updated passenger count {self.passenger_count} "
        )

    def offboard_all(self):
        floor = FLOOR_LIST.get_floor(self.floor)
        PASSENGERS.update_arrival(self.passengers)

        import time
        from metrics.BoardingTime import boarding_time

        num_to_offboard = self.passenger_count
        if num_to_offboard == 0:
            return None
        time_to_offboard = boarding_time(self, num_to_offboard, num_to_offboard, 0)
        if time_to_offboard > 0:
            self.detail_log(f'offboarding {num_to_offboard} passengers takes {time_to_offboard} s')
            time.sleep(time_to_offboard)

        self.log(
            f"{self.name}: "
            f"Offboarding {num_to_offboard} passengers "
            f"at floor {floor.name}"
        )
        self.passengers.remove_all_passengers()
        self.calculate_passenger_count()
        self.log(
            f"{self.name}: "
            f"Updated passenger count {self.passenger_count} "
        )

    def offboard_arrived(self):
        current_floor = FLOOR_LIST.get_floor(self.floor)
        to_offboard = self.passengers.filter_by_destination(current_floor)

        import time
        from metrics.BoardingTime import boarding_time

        num_to_offboard = to_offboard.count_passengers()
        if num_to_offboard == 0:
            return None
        time_to_offboard = boarding_time(self, self.passenger_count, num_to_offboard, 0)
        if time_to_offboard > 0:
            self.detail_log(f'offboarding {num_to_offboard} passengers takes {time_to_offboard} s')
            time.sleep(time_to_offboard)

        self.log(
            f"{self.name}: "
            f"Offboarding {num_to_offboard} passengers "
            f"at floor {current_floor.name}"
        )
        self.passengers.remove_passengers(to_offboard)
        self.calculate_passenger_count()
        PASSENGERS.update_arrival(to_offboard)
        self.calculate_passenger_count()
        self.log(
            f"{self.name}: "
            f"Updated passenger count {self.passenger_count} "
        )

    # to test
    async def move(self, floor):
        "moves to floor, assumes it is on a stopped state"
        current_floor = FLOOR_LIST.get_floor(self.floor)
        time_to_move = self.calc_time_to_move(current_floor, floor)
        self.detail_log(f'time to move is {time_to_move}')
        if floor.height > self.height:
            self.dir = 'U'
        elif floor.height < self.height:
            self.dir = 'D'
        else:
            self.dir = 'S'
        self.log(
            f"{self.name}: "
            f"Start move from {current_floor.name} "
            f"height {current_floor.height} "
            f"at dir {self.dir}"
        )

        start_move_time = datetime.now()
        try:
            async with asyncio.timeout(time_to_move):
                # TODO: error due to await of generator
                new_source, new_target_floor, new_dir = await PASSENGERS.register_arrivals()
                if self.is_within_next_target(current_floor, floor, self.dir, new_source, new_dir) and self.has_capacity():
                    time_elapsed = datetime.now() - start_move_time
                    moving_status = self.get_moving_status_from_floor(time_elapsed, current_floor, floor)
                    redirect = self.calc_is_floor_reachable_while_moving(moving_status, new_source)
                    if redirect:
                        time_to_move = self.calc_time_to_move_while_moving(moving_status, new_target_floor)
                        arrival_time = asyncio.get_running_loop().time() + time_to_move
                        asyncio.Timeout.reschedule(arrival_time)
                        floor = new_target_floor
        except asyncio.TimeoutError:
            if floor.floor == MIN_FLOOR:
                self.dir = 'U'
            elif floor.floor == MAX_FLOOR:
                self.dir = 'D'
            
            self.log(
                f"{self.name}: "
                f"Stop move at {floor.name} "
                f"height {floor.height} "
            )
            self.floor = floor.floor
            self.height = floor.height
            self.passengers.update_passenger_floor(floor)
            PASSENGERS.update_lift_passenger_floor(self, floor)

        
    # def move(self, floor):
    #     "moves to floor, assumes it is on a stopped state"
    #     current_floor = FLOOR_LIST.get_floor(self.floor)
    #     time_to_move = self.calc_time_to_move(current_floor, floor)
    #     self.detail_log(f'time to move is {time_to_move}')
    #     if floor.height > self.height:
    #         self.dir = 'U'
    #     elif floor.height < self.height:
    #         self.dir = 'D'
    #     else:
    #         self.dir = 'S'
    #     self.log(
    #         f"{self.name}: "
    #         f"Start move from {current_floor.name} "
    #         f"height {current_floor.height} "
    #         f"at dir {self.dir}"
    #     )

    #     import time
    #     time.sleep(time_to_move)

    #     if floor.name == MIN_FLOOR:
    #         self.dir = 'U'
    #     elif floor.name == MAX_FLOOR:
    #         self.dir = 'D'
        
    #     self.log(
    #         f"{self.name}: "
    #         f"Stop move at {floor.name} "
    #         f"height {floor.height} "
    #     )
    #     self.floor = floor.name
    #     self.height = floor.height
    #     self.passengers.update_passenger_floor(floor)
    #     PASSENGERS.update_lift_passenger_floor(self, floor)

    def calc_time_to_move(self, old_floor, new_floor):
        "distance lookup function takes into account time for acceleration and deceleration"

        new_height = new_floor.height
        old_height = old_floor.height
        distance = abs( new_height - old_height)
        return self.model.calc_time(distance)
    
    def get_moving_status_from_floor(self, time_elapsed, source_floor, target_floor):
        moving_status = CalcMovingFloor(
            source=source_floor.name,
            target=target_floor.name,
            lift_spec=self.model
        )
        return moving_status.calc_state(time_elapsed)

    # to init test
    def calc_time_to_move_from_floor(self, time_elapsed, source_floor, target_floor, proposed_floor):
        assert self.model.model_type == "accel"

        height, direction, velocity = self.get_moving_status_from_floor(time_elapsed, source_floor, target_floor)

        from metrics.CalcAccelModelMovingStatus import CalcAccelModelMovingStatus
        moving_status = CalcAccelModelMovingStatus(height, direction, velocity, self.model)

        return self.calc_time_to_move_while_moving(moving_status, proposed_floor)
    
    # to init test
    def calc_time_to_move_while_moving(self, moving_status, proposed_floor):
        proposed_floor_height = FLOOR_LIST.get_floor(proposed_floor).height

        return moving_status.calc_time(proposed_floor_height)
    
    # to init test
    def calc_is_floor_reachable_while_moving(self, moving_status, proposed_floor):
        proposed_floor_height = FLOOR_LIST.get_floor(proposed_floor).height

        return moving_status.get_stoppability(proposed_floor_height)

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
        
    def is_within_next_target(self, current_floor, current_target, dir, proposed_target, proposed_dir):
        "assumes current move is for existing passengers, not a preempting move"
        if proposed_dir != dir:
            return False
        if dir == 'U':
            return (
                current_target > current_floor
            ) and (
                proposed_target < current_target
            )
        elif dir == 'D':
            return (
                current_target < current_floor
            ) and (
                proposed_target > current_target
            )
        return False
    
    async def lift_baseline_operation(self):
        next_target = self.next_baseline_target()
        print(f'lift next target {next_target}')
        while True:
            if next_target is not None:
                print(f'lift moving to target {next_target}')
                next_floor = FLOOR_LIST.get_floor(next_target)
                await self.move(next_floor)
                print(f'lift moved to target {next_target}')
                next_target = self.next_baseline_target()
                print(f'lift new next target {next_target}')
            else:
                next_target = self.next_baseline_target()
