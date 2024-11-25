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
from metrics.CalcAccelModelMovingStatus import CalcAccelModelMovingStatus

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

    def has_floor_capacity(self, direction):
        floor_count = self.get_current_floor().get_floor_passenger_count_with_dir(direction)
        return self.passenger_count + floor_count <= self.capacity

    async def onboard_all(self):
        floor = self.get_current_floor()
        PASSENGERS.assign_lift_for_floor(self, floor)
        PASSENGERS.board(PASSENGERS.filter_by_floor(floor))

        from metrics.BoardingTime import boarding_time

        num_to_onboard = floor.passengers.count_passengers()
        if num_to_onboard == 0:
            return None
        time_to_onboard = boarding_time(self, self.passenger_count, 0, num_to_onboard)
        if time_to_onboard > 0:
            self.detail_log(f'onboarding {num_to_onboard} passengers takes {time_to_onboard} s')
            await asyncio.sleep(time_to_onboard)

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

    async def onboard_random_available(self):
        floor = FLOOR_LIST.get_floor(self.floor)
        if self.has_floor_capacity(self.dir):
            selection = floor.passengers.df
        else:
            selection = floor.random_select_passengers(self.capacity, self.passenger_count)
        passenger_list = PassengerList(selection)

        from metrics.BoardingTime import boarding_time

        num_to_onboard = passenger_list.count_passengers()
        if num_to_onboard == 0:
            return None
        time_to_onboard = boarding_time(self, self.passenger_count, 0, num_to_onboard)
        if time_to_onboard > 0:
            self.detail_log(f'onboarding {num_to_onboard} passengers takes {time_to_onboard} s')
            await asyncio.sleep(time_to_onboard)

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

    async def onboard_earliest_arrival(self):
        floor = FLOOR_LIST.get_floor(self.floor)
        if self.has_floor_capacity(self.dir):
            selection = floor.passengers.filter_by_direction(self.dir).df
        else:
            selection = floor.select_passengers_with_dir_by_earliest_arrival(self.dir, self.capacity, self.passenger_count)
        passenger_list = PassengerList(selection)

        import time
        from metrics.BoardingTime import boarding_time

        num_to_onboard = passenger_list.count_passengers()
        if num_to_onboard == 0:
            return None
        time_to_onboard = boarding_time(self, self.passenger_count, 0, num_to_onboard)
        if time_to_onboard > 0:
            self.detail_log(f'onboarding {num_to_onboard} passengers takes {time_to_onboard} s')
            await asyncio.sleep(time_to_onboard)

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

    async def offboard_all(self):
        floor = FLOOR_LIST.get_floor(self.floor)
        PASSENGERS.update_arrival(self.passengers)

        from metrics.BoardingTime import boarding_time

        num_to_offboard = self.passenger_count
        if num_to_offboard == 0:
            return None
        time_to_offboard = boarding_time(self, num_to_offboard, num_to_offboard, 0)
        if time_to_offboard > 0:
            self.detail_log(f'offboarding {num_to_offboard} passengers takes {time_to_offboard} s')
            await asyncio.sleep(time_to_offboard)

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

    async def offboard_arrived(self):
        current_floor = FLOOR_LIST.get_floor(self.floor)
        to_offboard = self.passengers.filter_by_destination(current_floor)

        from metrics.BoardingTime import boarding_time

        num_to_offboard = to_offboard.count_passengers()
        if num_to_offboard == 0:
            return None
        time_to_offboard = boarding_time(self, self.passenger_count, num_to_offboard, 0)
        if time_to_offboard > 0:
            self.detail_log(f'offboarding {num_to_offboard} passengers takes {time_to_offboard} s')
            await asyncio.sleep(time_to_offboard)

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
        print('schedule to arrive in', round(time_to_move, 2))
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

        time_prev = datetime.now()
        after_redirect = False
        try:
            async with asyncio.timeout(time_to_move) as timeout:
                while True:
                    pa_queue = PASSENGERS.arrival_queue
                    pa_trigger = asyncio.wait_for(pa_queue.get(), timeout=None)
                    new_source, new_target_floor, new_dir = await pa_trigger
                    if  (
                        self.has_capacity() and 
                        self.is_within_next_target(current_floor, floor, self.dir, 
                                                   FLOOR_LIST.get_floor(new_source), new_dir)
                    ):
                        time_elapsed = (datetime.now() - time_prev).total_seconds()
                        if not after_redirect:
                            h, d, v  = self.get_moving_status_from_floor(time_elapsed, current_floor, floor)
                        else:
                            # TODO: calculate moving status for redirects
                            h, d, v = self.get_moving_status_after_redirect(time_elapsed, moving_status, floor)
                        moving_status = CalcAccelModelMovingStatus(h, d, v, self.model)
                        redirect = self.calc_is_floor_reachable_while_moving(moving_status, new_source)
                        if redirect:
                            time_to_move = self.calc_time_to_move_while_moving(moving_status, new_source)
                            new_arrival_time = asyncio.get_running_loop().time() + time_to_move
                            timeout.reschedule(new_arrival_time)
                            floor = FLOOR_LIST.get_floor(new_source)
                            print('redirect to floor', floor.name, 'after', datetime.now()-time_prev)
                            print('schedule to arrive in', round(time_to_move, 2))
                            after_redirect = True
        except asyncio.TimeoutError:
            # to test
            # only one floor with passengers
            if self.floor == floor.name:
                single_floor_dir = self.find_single_floor()
                if single_floor_dir is not None:
                    self.dir = single_floor_dir
                print(self.name, 'direction is', self.dir)
                self.log(f"{self.name} direction is {self.dir}")
            if floor.name == self.find_furthest_target():
                if self.dir == 'D':
                    self.dir = 'U'
                elif self.dir == 'U':
                    self.dir = 'D'
                print(self.name, 'direction is', self.dir)
                self.log(f"{self.name} direction is {self.dir}")
            
            self.log(
                f"{self.name}: "
                f"Stop move at {floor.name} "
                f"height {floor.height} "
            )
            print('stop at floor', floor.name)
            self.floor = floor.name
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
    
    def get_moving_status_after_redirect(self, time_elapsed, moving_status, target_floor):
        return moving_status.calc_status(target_floor.height, time_elapsed)

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
        # print('next baseline target with', overall_targets, 'at dir', self.dir, self.floor)
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
                return floor_scan.lift_target.max()

            floor_scan = targets.loc[
                (targets.dir == 'U'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.lift_target.min()

            return targets.lift_target.max()
        
    def find_furthest_target(self):
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
        # print('next baseline target with', overall_targets, 'at dir', self.dir, self.floor)
        return self.find_furthest_floor(overall_targets)
        
    def find_single_floor(self):
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
        if overall_targets.shape[0] == 1:
            return overall_targets.iloc[0].dir
        else:
            return None
    
    # # to test
    # def furthest_boarded_target(self):
    #     """
    #     baseline for lift target algorithm
    #     attends to the most immediate request
    #     """
    #     lift_targets = self.passengers.passenger_target_scan().rename(
    #         columns={'target': 'lift_target'}
    #     )
    #     return self.find_furthest_floor(lift_targets)
    
    # # to test
    def find_furthest_floor(self, targets):
        if targets.shape[0] == 0:
            return None
        if self.dir == 'U':
            return targets.lift_target.max()
        elif self.dir == 'D':
            return targets.lift_target.min()
        
    # # to test
    # def is_beyond_all_targets(self, new_target):
    #     if self.dir == 'U':
    #         return new_target > self.furthest_boarded_target()
    #     elif self.dir == 'D':
    #         return new_target < self.furthest_boarded_target()
        
    def is_within_next_target(self, current_floor, current_target, dir, proposed_target, proposed_dir):
        "assumes current move is for existing passengers, not a preempting move"
        if proposed_dir != dir:
            return False
        if dir == 'U':
            return (
                current_target.height > current_floor.height
            ) and (
                proposed_target.height < current_target.height
            )
        elif dir == 'D':
            return (
                current_target.height < current_floor.height
            ) and (
                proposed_target.height > current_target.height
            )
        return False
    
    async def lift_baseline_operation(self):
        print('start baseline operation')
        next_target = self.next_baseline_target()
        print(f'lift next target {next_target}')
        while True:
            if next_target is not None:
                print(f'lift moving to target {next_target}')
                next_floor = FLOOR_LIST.get_floor(next_target)
                await self.move(next_floor)
                await self.loading(print_stats=True)
                print(f'lift moved to target {self.floor}')
                next_target = self.next_baseline_target()
                print(f'lift new next target {next_target}')
            else:
                next_target = self.next_baseline_target()
                await asyncio.sleep(0)
    
    async def loading(self, print_stats = False):
        await self.offboard_arrived()
        await self.onboard_earliest_arrival()
        if print_stats:
            print('l1', self.passengers.df.iloc[:,:9])
        PASSENGERS.update_passenger_metrics()
        if print_stats:
            print('PASSENGERS', PASSENGERS.df.iloc[:,:9] \
                  .sort_values(by=['dir', 'current', 'status', 'trip_start_time']))
