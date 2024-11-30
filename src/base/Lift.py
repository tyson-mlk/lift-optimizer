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
        self.next_dir = None # store for dir of next target
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

    def has_floor_capacity(self, floor=None, direction=None):
        if floor is None:
            floor = self.get_current_floor()
        if direction is None:
            direction = self.dir

        floor_count = floor.get_floor_passenger_count_with_dir(direction)
        return self.passenger_count + floor_count <= self.capacity
    
    def has_capacity_for(self, passenger_selection):
        return self.passenger_count + passenger_selection.count_passengers() <= self.capacity
    
    def is_vacant(self):
        return self.passenger_count == 0

    async def onboard_all(self, bypass_prev_assignment=True):
        """onboard all passengers on the same floor without regarding lift capacity"""
        floor = self.get_current_floor()
        # assign lift
        if bypass_prev_assignment:
            passengers_to_assign = PASSENGERS.filter_by_status_waiting() \
                .filter_by_floor(floor)
            PASSENGERS.assign_lift_for_selection(self, passengers_to_assign, assign_multi=False)
        else:
            passengers_to_assign = PASSENGERS.filter_by_status_waiting() \
                .filter_by_floor(floor) \
                .filter_by_lift_assigned_not_to_other_only(self)
            PASSENGERS.assign_lift_for_selection(self, passengers_to_assign, assign_multi=False)
        # board
        PASSENGERS.board(passengers_to_assign.filter_by_floor(floor))
        num_to_onboard = passengers_to_assign.count_passengers()
        if num_to_onboard == 0:
            return None

        from metrics.BoardingTime import boarding_time

        # wait boarding time
        time_to_onboard = boarding_time(self, self.passenger_count, 0, num_to_onboard)
        if time_to_onboard > 0:
            self.detail_log(f'onboarding {num_to_onboard} passengers takes {time_to_onboard} s')
            await asyncio.sleep(time_to_onboard)

        self.log(f"{self.name}: Onboarding {num_to_onboard} passengers at floor {floor.name}")
        self.passengers.bulk_add_passengers(passengers_to_assign)
        self.passengers.assign_lift(self, assign_multi=False)
        self.passengers.board(passengers_to_assign)
        floor.onboard_selected(passengers_to_assign)
        floor.log(f"{floor.name}: {num_to_onboard} passengers boarded")
        floor.log(f"{floor.name}: passenger count is {floor.passengers.count_passengers()}")
        self.calculate_passenger_count()
        self.log(f"{self.name}: Updated passenger count {self.passenger_count}")

    async def onboard_random_available(self, bypass_prev_assignment=True):
        "onboards passengers on the same floor by random if capacity is insufficient"
        floor = FLOOR_LIST.get_floor(self.floor)
        if bypass_prev_assignment:
            eligible_passengers = PASSENGERS.filter_by_status_waiting() \
                .filter_by_floor(floor) \
                .filter_by_direction(self.dir)
        else:
            eligible_passengers = PASSENGERS.filter_by_status_waiting() \
                .filter_by_floor(floor) \
                .filter_by_direction(self.dir) \
                .filter_by_lift_assigned_not_to_other_only(self)
        if self.has_capacity_for(eligible_passengers):
            selection = eligible_passengers.df
        else:
            selection = eligible_passengers.sample_passengers(self.capacity - self.passenger_count)
        passenger_list = PassengerList(selection)

        from metrics.BoardingTime import boarding_time

        num_to_onboard = passenger_list.count_passengers()
        if num_to_onboard == 0:
            return None
        time_to_onboard = boarding_time(self, self.passenger_count, 0, num_to_onboard)
        if time_to_onboard > 0:
            self.detail_log(f'onboarding {num_to_onboard} passengers takes {time_to_onboard} s')
            await asyncio.sleep(time_to_onboard)

        self.log(f"{self.name}: Onboarding {num_to_onboard} passengers at floor {floor.name}")
        PASSENGERS.assign_lift_for_selection(self, passenger_list, assign_multi=False)
        PASSENGERS.board(passenger_list)
        floor.onboard_selected(passenger_list)
        floor.log(f"{floor.name}: {num_to_onboard} passengers boarded")
        floor.log(f"{floor.name}: passenger count is {floor.passengers.count_passengers()}")
        self.passengers.bulk_add_passengers(passenger_list)
        self.passengers.assign_lift(self, assign_multi=False)
        self.passengers.board(passenger_list)
        self.calculate_passenger_count()
        self.log(f"{self.name}: Updated passenger count {self.passenger_count}")

    async def onboard_earliest_arrival(self, next_dir, bypass_prev_assignment=True):
        "onboards passengers on the same floor by earliest assignment if capacity is insufficient"
        floor = FLOOR_LIST.get_floor(self.floor)
        if bypass_prev_assignment:
            eligible_passengers = PASSENGERS.filter_by_status_waiting() \
                .filter_by_floor(floor) \
                .filter_by_direction(next_dir)
        else:
            eligible_passengers = PASSENGERS.filter_by_status_waiting() \
                .filter_by_floor(floor) \
                .filter_by_direction(next_dir) \
                .filter_by_lift_assigned_not_to_other_only(self)
        if self.has_capacity_for(eligible_passengers):
            selection = eligible_passengers.df
        else:
            selection = eligible_passengers.filter_dir_for_earliest_arrival(
                self.dir, self.capacity - self.passenger_count
            )
        passenger_list = PassengerList(selection)

        from metrics.BoardingTime import boarding_time

        num_to_onboard = passenger_list.count_passengers()
        if num_to_onboard == 0:
            return None
        time_to_onboard = boarding_time(self, self.passenger_count, 0, num_to_onboard)
        if time_to_onboard > 0:
            self.detail_log(f'onboarding {num_to_onboard} passengers takes {time_to_onboard} s')
            await asyncio.sleep(time_to_onboard)

        self.log(f"{self.name}: Onboarding {num_to_onboard} passengers at floor {floor.name}")
        PASSENGERS.assign_lift_for_selection(self, passenger_list, assign_multi=False)
        PASSENGERS.board(passenger_list)
        floor.onboard_selected(passenger_list)
        floor.log(f"{floor.name}: {num_to_onboard} passengers boarded")
        floor.log(f"{floor.name}: passenger count is {floor.passengers.count_passengers()}")
        self.passengers.bulk_add_passengers(passenger_list)
        self.passengers.assign_lift(self, assign_multi=False)
        self.passengers.board(passenger_list)
        self.calculate_passenger_count()
        self.log(f"{self.name}: Updated passenger count {self.passenger_count}")

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

        self.log(f"{self.name}: Offboarding {num_to_offboard} passengers at floor {floor.name}")
        self.passengers.remove_all_passengers()
        self.calculate_passenger_count()
        self.log(f"{self.name}: Updated passenger count {self.passenger_count}")

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

        self.log("{self.name}: Offboarding {num_to_offboard} passengers at floor {current_floor.name}")
        self.passengers.remove_passengers(to_offboard)
        self.calculate_passenger_count()
        PASSENGERS.update_arrival(to_offboard)
        self.log(f"{self.name}: Updated passenger count {self.passenger_count}")

    # to test
    async def move(self, floor, next_dir):
        "moves to floor, responds to new async requests"
        current_floor = FLOOR_LIST.get_floor(self.floor)
        time_to_move = self.calc_time_to_move(current_floor, floor)
        print(f'{self.name} schedule to arrive in {round(time_to_move, 2)}')
        self.detail_log(f'time to move is {time_to_move}')
        if floor.height > self.height:
            self.dir = 'U'
        elif floor.height < self.height:
            self.dir = 'D'
        else:
            self.dir = 'S'
        self.log(f"{self.name}: Start move from {current_floor.name} height {current_floor.height} at dir {self.dir}")

        time_since_latest_direction = datetime.now()
        after_redirect = False
        try:
            async with asyncio.timeout(time_to_move) as timeout:
                while True:
                    redirect = False
                    pa_queue = PASSENGERS.arrival_queue
                    pa_trigger = asyncio.wait_for(pa_queue.get(), other_lift_queue.get(), timeout=None)
                    new_source, new_target_floor, new_dir = await pa_trigger
                    print(f'{self.name} triggered', new_source, new_target_floor, new_dir)
                    if  (
                        self.has_capacity() and 
                        self.is_within_next_target(current_floor, floor, self.dir, 
                                                   FLOOR_LIST.get_floor(new_source), new_dir)
                    ):
                        time_elapsed = (datetime.now() - time_since_latest_direction).total_seconds()
                        if not after_redirect:
                            h, d, v  = self.get_moving_status_from_floor(time_elapsed, current_floor, floor)
                        else:
                            h, d, v = self.get_moving_status_after_redirect(time_elapsed, moving_status, floor)
                        moving_status = CalcAccelModelMovingStatus(h, d, v, self.model)
                        redirect = self.calc_is_floor_reachable_while_moving(moving_status, new_source)
                        if redirect:
                            time_to_move = self.calc_time_to_move_while_moving(moving_status, new_source)
                            new_arrival_time = asyncio.get_running_loop().time() + time_to_move
                            timeout.reschedule(new_arrival_time)
                            floor = FLOOR_LIST.get_floor(new_source)
                            self.log(f"{self.name} redirect to floor {floor.name} after {datetime.now()-time_since_latest_direction}")
                            print(self.name, 'redirect to floor', floor.name, 'after', datetime.now()-time_since_latest_direction)
                            self.update_next_dir(floor.name)
                            print(f'{self.name} lift next direction {self.next_dir}')
                            self.assign_passengers(floor.name, assign_multi=True)
                            self.detail_log(f"{self.name} schedule to arrive in {round(time_to_move, 2)}")
                            print(self.name, 'schedule to arrive in', round(time_to_move, 2))
                            time_since_latest_direction = datetime.now()
                            after_redirect = True
                    if not redirect:
                        msg = new_source, new_target_floor, new_dir
                        # TODO: add other lift queue to wait
                        other_lift_queue.put_nowait(msg)
                        # next next step to replace
                        next_lift = find_next_lift_to_search_redirect()
                        trigger_next_lift_queue(msg)
                        asyncio.sleep(0)
        except asyncio.TimeoutError:
            self.log(f"{self.name}: reached {floor.name} at height {floor.height}")
            if next_dir is None:
                if self.floor == floor.name:
                    single_floor_dir = self.find_single_passenger_floor()
                    if single_floor_dir is not None:
                        self.dir = single_floor_dir
                        self.log(f"{self.name}: lone floor directed to {self.dir}")
                elif self.dir in ['U', 'D']:
                    furthest_target, furthest_dir = self.find_furthest_target_dir()
                    if floor.name == furthest_target and self.dir != furthest_dir:
                        self.dir = furthest_dir
                        self.log(f"{self.name}: maximal floor turn back to {self.dir}")
            else:
                self.dir = next_dir
                self.log(f"{self.name}: next request dir {self.dir}")

            
            self.floor = floor.name
            self.height = floor.height
            self.passengers.update_passenger_floor(floor)
            PASSENGERS.update_lift_passenger_floor(self, floor)

        
    def manual_move(self, floor):
        "moves to floor in a single operation"
        current_floor = FLOOR_LIST.get_floor(self.floor)
        time_to_move = self.calc_time_to_move(current_floor, floor)
        self.detail_log(f'time to move is {time_to_move}')
        if floor.height > self.height:
            self.dir = 'U'
        elif floor.height < self.height:
            self.dir = 'D'
        else:
            self.dir = 'S'
        self.log(f"{self.name}: Start move from {current_floor.name} height {current_floor.height} at dir {self.dir}")

        import time
        time.sleep(time_to_move)

        self.log(f"{self.name}: reached {floor.name} at height {floor.height}")
        # print('reached floor', floor.name)
        if self.floor == floor.name:
            single_floor_dir = self.find_single_passenger_floor()
            if single_floor_dir is not None:
                self.dir = single_floor_dir
                self.log(f"{self.name}: lone floor directed to {self.dir}")
        elif self.dir in ['U', 'D']:
            furthest_target, furthest_dir = self.find_furthest_target_dir()
            if floor.name == furthest_target and self.dir != furthest_dir:
                self.dir = furthest_dir
                self.log(f"{self.name}: maximal floor turn back to {self.dir}")
        
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
    
    def get_moving_status_from_floor(self, time_elapsed, source_floor, target_floor):
        moving_status = CalcMovingFloor(
            source=source_floor.name,
            target=target_floor.name,
            lift_spec=self.model
        )
        return moving_status.calc_state(time_elapsed)
    
    def get_moving_status_after_redirect(self, time_elapsed, moving_status, target_floor):
        return moving_status.calc_status(target_floor.height, time_elapsed)

    def calc_time_to_move_from_floor(self, time_elapsed, source_floor, target_floor, proposed_floor):
        assert self.model.model_type == "accel"

        height, direction, velocity = self.get_moving_status_from_floor(time_elapsed, source_floor, target_floor)

        from metrics.CalcAccelModelMovingStatus import CalcAccelModelMovingStatus
        moving_status = CalcAccelModelMovingStatus(height, direction, velocity, self.model)

        return self.calc_time_to_move_while_moving(moving_status, proposed_floor)
    
    def calc_time_to_move_while_moving(self, moving_status, proposed_floor):
        proposed_floor_height = FLOOR_LIST.get_floor(proposed_floor).height

        return moving_status.calc_time(proposed_floor_height)
    
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
                return floor_scan.lift_target.max()

            floor_scan = targets.loc[
                (targets.dir == 'U'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.lift_target.min()

            return targets.lift_target.max()
        
    def find_furthest_target_dir(self):
        """
        baseline for lift target algorithm
        attends to the most immediate request
        """
        lift_targets = self.passengers.passenger_target_scan().rename(
            columns={'target': 'lift_target'}
        )
        to_exclude = (
            (lift_targets.lift_target == max(FLOOR_LIST.list_floors())) & (lift_targets.dir == 'U')
        ) | (
            (lift_targets.lift_target == min(FLOOR_LIST.list_floors())) & (lift_targets.dir == 'D')
        )
        lift_targets = lift_targets.loc[~to_exclude,:]
        passengers_in_wait = PassengerList(PASSENGERS.df.loc[PASSENGERS.df.lift == 'Unassigned', :])
        waiting_targets = passengers_in_wait.passenger_source_scan().rename(
            columns={'source': 'lift_target'}
        )
        overall_targets = pd.concat([lift_targets, waiting_targets])
        return self.find_furthest_floor_dir(overall_targets)
        
    def find_single_passenger_floor(self):
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
    
    def find_furthest_floor_dir(self, targets):
        if targets.shape[0] == 0:
            return None, None
        if self.dir == 'U':
            opp_dir = 'D'
            furthest = targets.lift_target.max()
        elif self.dir == 'D':
            opp_dir = 'U'
            furthest = targets.lift_target.min()
        
        if self.dir in targets.loc[targets.lift_target==furthest, 'dir'].values:
            return (furthest, self.dir)
        else:
            return (furthest, opp_dir)
        
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
    
    def update_next_dir(self, target_floor):
        if target_floor is None:
            self.next_dir = None
            return None
        # updates next floor and direction
        furthest_floor, furthest_dir = self.find_furthest_target_dir()
        if furthest_floor == None:
            self.next_dir = None
            return None
        if furthest_floor == target_floor and furthest_dir != self.dir:
            self.next_dir = 'D' if self.dir == 'U' else 'U'
        else:
            self.next_dir = self.dir
    
    def assign_passengers(self, target_floor, assign_multi=True):
        if target_floor is None:
            return None
        limit = self.capacity - self.get_total_assigned()
        # nothing more to assign
        if limit <= 0:
            return None
        # assigns waiting passengers and their floors to lifts
        floor = FLOOR_LIST.get_floor(target_floor)
        if assign_multi:
            assignment_list = PASSENGERS \
                .filter_by_status_waiting() \
                .filter_by_floor(FLOOR_LIST.get_floor(target_floor)) \
                .filter_by_direction(self.next_dir)
        else:
            assignment_list = PASSENGERS \
                .filter_by_status_waiting() \
                .filter_by_floor(FLOOR_LIST.get_floor(target_floor)) \
                .filter_by_direction(self.next_dir) \
                .filter_by_lift_unassigned()
        num_to_assign = min(assignment_list.count_passengers(), limit)
        assignment_list = assignment_list.filter_by_earliest_arrival(num_to_assign)
        PASSENGERS.assign_lift_for_selection(self, assignment_list)
        floor.passengers.assign_lift_for_selection(self, assignment_list)

    def get_total_assigned(self):
        non_arrived = PASSENGERS.df.loc[PASSENGERS.df.status != 'Arrived', :]
        return (non_arrived.lift == self.name).sum()
    
    # to test changes
    # TODO: prevent race condition
    async def lift_baseline_operation(self):
        """
        baseline operation
        variables:
        - next_target: target floor to move to; None if no request outstanding
        - next_dir: direction to take passengers afer moving to target; None if
        """
        print(f'{self.name} start baseline operation')
        await asyncio.sleep(0)
        next_target = self.next_baseline_target()
        print(f'{self.name} lift next target {next_target}')
        self.update_next_dir(next_target)
        print(f'{self.name} lift next direction {self.next_dir}')
        self.assign_passengers(next_target, assign_multi=True)
        # print('debug passenger assignment')
        # PASSENGERS.pprint_passenger_status(FLOOR_LIST, ordering_type='source')
        while True:
            if next_target is not None:
                # baseline allows multi assignment after floor is chosen
                print(f'{self.name} lift moving to target {next_target}')
                next_floor = FLOOR_LIST.get_floor(next_target)
                await self.move(next_floor, self.next_dir)
                print(f'{self.name} lift moved to target {self.floor} facing {self.dir}')
                self.debug_print_state()
                await self.loading(self.next_dir)
                print(f'{self.name} after loading, lift passengers:', self.passengers.df.index.values)
                await asyncio.sleep(0)
                # debug only
                self.debug_print_overall_stats()
                next_target = self.next_baseline_target()
                print(f'{self.name} lift new target {next_target}')
                self.update_next_dir(next_target)
                print(f'{self.name} lift next direction {self.next_dir}')
                self.assign_passengers(next_target, assign_multi=True)
                # print('debug passenger assignment')
                # PASSENGERS.pprint_passenger_status(FLOOR_LIST, ordering_type='source')
            else:
                await asyncio.sleep(0)
                next_target = self.next_baseline_target()
                if next_target is not None:
                    print(f'{self.name} lift new target {next_target}')
                    self.update_next_dir(next_target)        
                    print(f'{self.name} lift next direction {self.next_dir}')
                    self.assign_passengers(next_target, assign_multi=True)
                    # print('debug passenger assignment')
                    # PASSENGERS.pprint_passenger_status(FLOOR_LIST, ordering_type='source')
    
    async def loading(self, next_dir, print_lift_stats = False, print_passenger_stats=False):
        await self.offboard_arrived()
        await self.onboard_earliest_arrival(next_dir)
        PASSENGERS.update_passenger_metrics(print_passenger_stats, FLOOR_LIST)
        if print_lift_stats:
            self.pprint_current_passengers()

    def pprint_current_passengers(self):
        def passenger_time_format(t):
            return t.strftime("%H:%M:%S") if t is not pd.NaT else "NA"

        def format_start_time(df):
            return df.trip_start_time.apply(passenger_time_format)

        def format_board_time(df):
            return df.board_time.apply(passenger_time_format)
        
        df = self.passengers.df.copy()
        df['start_time'] = format_start_time(df)
        df['board_time'] = format_board_time(df)

        print_cols = ['source', 'start_time', 'board_time', 'target']
        print(f"{self.name} passengers on-board at {passenger_time_format(datetime.now())}")
        if self.passenger_count > 0:
            print(df.loc[:, print_cols])
        else:
            print('lift empty')

    def debug_print_state(self):
        print(f"{self.name} at floor {self.floor} with passengers: {self.passengers.df.index.values}")

    def debug_print_overall_stats(self):
        print('overall stats', PASSENGERS.df.groupby(['status', 'lift']).size().sort_index(level='status'))
