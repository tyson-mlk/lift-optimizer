import asyncio
import pandas as pd
from datetime import datetime, timedelta
from logging import INFO, DEBUG

from src.utils.Logging import get_logger, print_st
from src.base.Floor import Floor
from src.base.PassengerList import PassengerList, PASSENGERS
from src.base.FloorList import FLOOR_LIST, MAX_FLOOR, MIN_FLOOR
from src.metrics.LiftSpec import LiftSpec
from src.metrics.CalcMovingFloor import CalcMovingFloor
from src.metrics.CalcAccelModelMovingStatus import CalcAccelModelMovingStatus

LIFT_CAPACITY_DEFAULT = 12

class Lift:
    "lift class"

    def __init__(self, name, floorname, dir, capacity = LIFT_CAPACITY_DEFAULT, model = "accel", 
                 lift_managing=False, lift_tracking=True) -> None:
        self.name = name
        self.floor = floorname
        self.height = self.get_current_floor().height
        self.dir = dir
        self.next_dir = None # store for dir of next target
        self.capacity = capacity
        self.passenger_count = 0
        self.passengers: PassengerList = PassengerList(lift_managing=lift_managing, lift_tracking=lift_tracking)
        self.calculate_passenger_count()
        self.model = LiftSpec(model=model)
        # lift movement state
        self.next_height = self.height
        self.redirect_state = False
        self.floor_move_state = {
            'start_move_floor':self.floor,
            'target_floor': self.floor,
            'start_move_time': datetime.now()
        }
        self.loading_state = False
        self.arrival_queue = asyncio.Queue()
        self.reassignment_queue = asyncio.Queue()
        # logging
        logger = get_logger(name, self.__class__.__name__, INFO)
        detail_logger = get_logger(name+'_det', self.__class__.__name__, DEBUG)
        self.log = lambda msg: logger.info(msg)
        self.detail_log = lambda msg: detail_logger.debug(msg)
        self.log(f"{self.name}: init")

    def __del__(self):
        self.log(f"{self.name}: start destructing")
        while not self.arrival_queue.empty():
            msg = self.arrival_queue.get_nowait()
            self.log(f"{self.name}: flushing arrival_queue item {msg}")
        while not self.reassignment_queue.empty():
            msg = self.reassignment_queue.get_nowait()
            self.log(f"{self.name}: flushing reassignment_queue item {msg}")
        self.log(f"{self.name}: destruction complete")

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
    
    def is_stationed(self):
        return self.dir == 'S'
    
    def set_stationed(self):
        self.dir = 'S'
    
    async def assign_passengers_while_boarding(self, time_to_board):
        try:
            first_assignment = True
            time_left_for_boarding = time_to_board
            arrival_queue = self.arrival_queue
            boarding_time_from = datetime.now()
            while True:
                pa_trigger = asyncio.wait_for(arrival_queue.get(), timeout=time_left_for_boarding)
                self.log(f'{self.name} pending arrivals while boarding')
                triggered = False
                new_source, _, new_dir = await pa_trigger
                triggered = True
                self.log(f'{self.name}. evaluating while loading {new_source, _, new_dir}')
                current_floor = FLOOR_LIST.get_floor(self.floor)
                floor = FLOOR_LIST.get_floor(new_source)
                if self.floor != new_source:
                    current_target = FLOOR_LIST.get_floor(self.loading_state['current_target'])
                    if current_target is None:
                        self.detail_log(f'{self.name} debugging loading_state None')
                    if (
                        current_target is None or
                        self.is_within_next_target(current_floor, current_target, self.next_dir, floor, new_dir)
                    ):
                        new_target = self.precalc_next_target_after_loading()
                        self.update_next_dir(new_target)
                        if new_target is not None:
                            self.detail_log(f'{self.name} loading_state current_target set to {new_target}')
                            self.loading_state['current_target'] = new_target
                        self.assign_passengers(new_target, assign_multi=True)
                        if not first_assignment:
                            self.unassign_passengers(prev_new_source, prev_new_dir)

                        self.log(f'{self.name} arrival calc True')
                        PASSENGERS.lift_msg_queue.put_nowait(True)
                        triggered = False
                        await asyncio.sleep(0)

                        first_assignment = False
                        prev_new_source, prev_new_dir = new_target, self.next_dir

                        time_now = datetime.now()
                        time_taken_to_arrive = (time_now - boarding_time_from).total_seconds()
                        self.log(f"{self.name}: at floor {self.floor} facing {self.dir} "
                                 f"while loading assigned to floor {floor.name} dir {self.next_dir} "
                                 f"after {time_taken_to_arrive}")
                        boarding_time_from = time_now
                        time_left_for_boarding -= time_taken_to_arrive
                        if time_left_for_boarding <= 0:
                            break # break while-loop
                        else:
                            continue # continue while-loop
                self.log(f'{self.name} arrival calc False')
                PASSENGERS.lift_msg_queue.put_nowait(False)
                triggered = False
                await asyncio.sleep(0)
                time_now = datetime.now()
                time_taken = (time_now - boarding_time_from).total_seconds()
                boarding_time_from = time_now
                time_left_for_boarding -= time_taken
                if time_left_for_boarding <= 0:
                    break
                else:
                    continue
        except asyncio.TimeoutError:
            self.log(f'{self.name} arrival calc timeout')
            # does it ever enter here
            if triggered:
                PASSENGERS.lift_msg_queue.put_nowait(False)
                self.log('lift_msg_queue to release arrival queue')
            await asyncio.sleep(0)
            self.log(f'{self.name} finish boarding')
    
    def precalc_num_to_onboard(self, onboarding_mode, bypass_prev_assignment=True, return_index=False):
        """
        preliminary calculation for number of passengers to onboard
        this may not be accurate as passenger state may have changed when onboarding
        """
        floor = self.get_current_floor()
        if onboarding_mode == 'all':
            if bypass_prev_assignment:
                passengers_to_assign = PASSENGERS.filter_by_status_waiting() \
                    .filter_by_floor(floor)
            else:
                passengers_to_assign = PASSENGERS.filter_by_status_waiting() \
                    .filter_by_floor(floor) \
                    .filter_by_lift_assigned_not_to_other_only(self)
            return passengers_to_assign.count_passengers()
        else:
            if bypass_prev_assignment:
                eligible_passengers = PASSENGERS.filter_by_status_waiting() \
                    .filter_by_floor(floor) \
                    .filter_by_direction(self.next_dir)
            else:
                eligible_passengers = PASSENGERS.filter_by_status_waiting() \
                    .filter_by_floor(floor) \
                    .filter_by_direction(self.next_dir) \
                    .filter_by_lift_assigned_not_to_other_only(self)
            if self.has_capacity_for(eligible_passengers):
                selection = eligible_passengers.df
            else:
                if onboarding_mode == 'random':
                    selection = eligible_passengers.sample_passengers(self.capacity - self.passenger_count)
                elif onboarding_mode == 'earliest':
                    selection = eligible_passengers.filter_dir_for_earliest_arrival(
                        self.dir, self.capacity - self.passenger_count
                    )
                else:
                    raise ValueError('Invalid onboarding_mode')
            passenger_list = PassengerList(selection)
            if return_index:
                return passenger_list.df.index
            return passenger_list.count_passengers()

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

        from src.metrics.BoardingTime import boarding_time

        # wait boarding time
        time_to_onboard = boarding_time(self, self.passenger_count, 0, num_to_onboard)

        self.passengers.bulk_add_passengers(passengers_to_assign)
        self.passengers.assign_lift(self, assign_multi=False)
        self.passengers.board(passengers_to_assign)
        floor.onboard_selected(passengers_to_assign)
        floor.log(f"{floor.name}: {num_to_onboard} passengers boarded")
        floor.log(f"{floor.name}: passenger count is {floor.passengers.count_passengers()}")
        self.calculate_passenger_count()
        self.log(f"{self.name}: Updated passenger count {self.passenger_count}")

        if time_to_onboard > 0:
            self.detail_log(f'{self.name}: onboarding {num_to_onboard} passengers takes {time_to_onboard} s')
            await asyncio.sleep(time_to_onboard)
        self.log(f"{self.name}: Onboarding {num_to_onboard} passengers at floor {floor.name}")
        print_st(f"{num_to_onboard} passengers boarded {self.name} at {floor.name}")

    async def onboard_random_available(self, bypass_prev_assignment=True):
        "onboards passengers on the same floor by random if capacity is insufficient"
        floor = FLOOR_LIST.get_floor(self.floor)
        if bypass_prev_assignment:
            eligible_passengers = PASSENGERS.filter_by_status_waiting() \
                .filter_by_floor(floor) \
                .filter_by_direction(self.next_dir)
        else:
            eligible_passengers = PASSENGERS.filter_by_status_waiting() \
                .filter_by_floor(floor) \
                .filter_by_direction(self.next_dir) \
                .filter_by_lift_assigned_not_to_other_only(self)
        if self.has_capacity_for(eligible_passengers):
            selection = eligible_passengers.df
        else:
            selection = eligible_passengers.sample_passengers(self.capacity - self.passenger_count)
        passenger_list = PassengerList(selection)

        from src.metrics.BoardingTime import boarding_time

        num_to_onboard = passenger_list.count_passengers()
        if num_to_onboard == 0:
            return None
        time_to_onboard = boarding_time(self, self.passenger_count, 0, num_to_onboard)

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

        if time_to_onboard > 0:
            self.detail_log(f'{self.name}: onboarding {num_to_onboard} passengers takes {time_to_onboard} s')
            await asyncio.sleep(time_to_onboard)
        self.log(f"{self.name}: Onboarding {num_to_onboard} passengers at floor {floor.name}")
        print_st(f"{num_to_onboard} passengers boarded {self.name} at {floor.name}")

    async def onboard_earliest_arrival(self, bypass_prev_assignment=True):
        "onboards passengers on the same floor by earliest assignment if capacity is insufficient"
        floor = FLOOR_LIST.get_floor(self.floor)
        if bypass_prev_assignment:
            eligible_passengers = PASSENGERS.filter_by_status_waiting() \
                .filter_by_floor(floor) \
                .filter_by_direction(self.next_dir)
        else:
            eligible_passengers = PASSENGERS.filter_by_status_waiting() \
                .filter_by_floor(floor) \
                .filter_by_direction(self.next_dir) \
                .filter_by_lift_assigned_not_to_other_only(self)
        if self.has_capacity_for(eligible_passengers):
            selection = eligible_passengers.df
        else:
            selection = eligible_passengers.filter_dir_for_earliest_arrival(
                self.dir, self.capacity - self.passenger_count
            )
        passenger_list = PassengerList(selection)
        
        from src.metrics.BoardingTime import boarding_time

        num_to_onboard = passenger_list.count_passengers()
        if num_to_onboard == 0:
            return None
        time_to_board = boarding_time(self, self.passenger_count, 0, num_to_onboard)

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

        if time_to_board > 0:
            self.detail_log(f'{self.name}: onboarding {num_to_onboard} passengers takes {time_to_board} s')
        await self.assign_passengers_while_boarding(time_to_board)
        self.log(f"{self.name}: Onboarding {num_to_onboard} passengers at floor {floor.name}")
        print_st(f"{num_to_onboard} passengers boarded {self.name} at {floor.name}")

    def precalc_num_to_offboard(self, offboarding_mode):
        if offboarding_mode == 'all':
            return self.passenger_count
        elif offboarding_mode == 'arrived':
            current_floor = FLOOR_LIST.get_floor(self.floor)
            to_offboard = self.passengers.filter_by_destination(current_floor)

            return to_offboard.count_passengers()

    async def offboard_all(self):
        floor = FLOOR_LIST.get_floor(self.floor)
        PASSENGERS.update_arrival(self.passengers)

        from src.metrics.BoardingTime import boarding_time

        num_to_offboard = self.passenger_count
        if num_to_offboard == 0:
            return None
        time_to_offboard = boarding_time(self, num_to_offboard, num_to_offboard, 0)
        if time_to_offboard > 0:
            self.detail_log(f'{self.name}: offboarding {num_to_offboard} passengers takes {time_to_offboard} s')
            await asyncio.sleep(time_to_offboard)

        self.log(f"{self.name}: Offboarding {num_to_offboard} passengers at floor {floor.name}")
        self.passengers.remove_all_passengers()
        self.calculate_passenger_count()
        self.log(f"{self.name}: Updated passenger count {self.passenger_count}")
        print_st(f"{num_to_offboard} passengers offboarded {self.name}")

    async def offboard_arrived(self):
        current_floor = FLOOR_LIST.get_floor(self.floor)
        to_offboard = self.passengers.filter_by_destination(current_floor)

        from src.metrics.BoardingTime import boarding_time

        num_to_offboard = to_offboard.count_passengers()
        if num_to_offboard == 0:
            return None
        time_to_board = boarding_time(self, self.passenger_count, num_to_offboard, 0)
        if time_to_board > 0:
            self.detail_log(f'{self.name}: offboarding {num_to_offboard} passengers takes {time_to_board} s')
        await self.assign_passengers_while_boarding(time_to_board)

        self.log(f"{self.name}: Offboarding {num_to_offboard} passengers at floor {current_floor.name}")
        self.passengers.remove_passengers(to_offboard)
        self.calculate_passenger_count()
        PASSENGERS.update_arrival(to_offboard)
        self.log(f"{self.name}: Updated passenger count {self.passenger_count}")
        print_st(f"{num_to_offboard} passengers offboarded {self.name} at {current_floor.name}")

    def precalc_loading_time(self, offboarding_mode, onboarding_mode):
        num_to_offboard = self.precalc_num_to_offboard(offboarding_mode=offboarding_mode)
        num_to_onboard = self.precalc_num_to_onboard(onboarding_mode=onboarding_mode)

        from src.metrics.BoardingTime import boarding_time

        time_to_onboard = boarding_time(self, self.passenger_count, 0, num_to_onboard)
        time_to_offboard = boarding_time(self, self.passenger_count, num_to_offboard, 0)

        return time_to_offboard + time_to_onboard

    async def move(self, floor):
        "moves to floor, responds to new async requests"
        current_floor = FLOOR_LIST.get_floor(self.floor)
        time_to_move = self.calc_time_to_move(current_floor, floor)
        time_to_arrive = datetime.now() + timedelta(seconds=time_to_move)
        self.detail_log(f'{self.name} schedule to arrive at {floor.name} in {round(time_to_move, 2)}')
        if floor.height > self.height:
            self.dir = 'U'
        elif floor.height < self.height:
            self.dir = 'D'
        self.next_height = floor.height
        self.log(f"{self.name}: Start move from {current_floor.name} height {current_floor.height} at dir {self.dir}")

        time_since_latest_move = datetime.now()
        self.floor_move_state = {
            'start_move_floor':self.floor,
            'target_floor': floor.name,
            'start_move_time': time_since_latest_move
        }
        try:
            while True:
                redirect = False
                arrival_queue = self.arrival_queue
                pa_trigger = asyncio.wait_for(arrival_queue.get(), timeout=time_to_move)
                self.log(f'{self.name} pending arrivals while moving')
                triggered = False
                new_source, _, new_dir = await pa_trigger
                triggered = True
                self.log(f'{self.name} arrival queue while moving {new_source, _, new_dir}')
                if  (
                    self.has_capacity() and 
                    self.is_within_next_target(current_floor, floor, self.dir, 
                                                FLOOR_LIST.get_floor(new_source), new_dir) and
                    PASSENGERS.filter_by_floor(FLOOR_LIST.get_floor(new_source)).filter_by_direction(new_dir) \
                        .filter_by_lift_unassigned().filter_by_status_waiting().count_passengers() > 0
                ):
                    time_elapsed = (datetime.now() - time_since_latest_move).total_seconds()
                    moving_status = self.get_moving_status_in_loop(time_elapsed, floor)
                    redirect = self.calc_is_floor_reachable_while_moving(moving_status, new_source)
                    if redirect:
                        prev_floor = floor
                        floor = FLOOR_LIST.get_floor(new_source)
                        self.update_next_dir(floor.name)
                        print_st(f'Redirecting {self.name} to {floor.name}')
                    self.log(f'{self.name} redirect is {redirect}')
                    if redirect:
                        # release prev assignment (operation sequence is for async not distributed)
                        if new_source != prev_floor.name:
                            self.unassign_passengers(prev_floor.name, self.next_dir)
                            unassigned_passengers = PASSENGERS.filter_by_status_waiting().filter_by_lift_unassigned() \
                                .filter_by_floor(prev_floor).filter_by_direction(self.next_dir)
                            self.log(f'unassigned passengers {unassigned_passengers.df.index}')

                        # assign new floor passengers (operation sequence is for async not distributed)
                        time_taken = (datetime.now()-time_since_latest_move).total_seconds()
                        self.log(f"{self.name} redirect to floor {floor.name} dir {self.next_dir} "
                                    f"after {round(time_taken, 2)}")
                        self.assign_passengers(floor.name, assign_multi=True)

                        # # perform redirection
                        # time_to_move = self.calc_time_to_move_while_moving(moving_status, new_source)
                        # new_arrival_time = asyncio.get_running_loop().time() + time_to_move
                        # timeout.reschedule(new_arrival_time)
                        # self.detail_log(f"{self.name} schedule to arrive in {round(time_to_move, 2)}")

                        # update lift state
                        time_since_latest_move = datetime.now()
                        self.redirect_state = {
                            'moving_status': moving_status,
                            'target_floor': floor.name,
                            'time_of_redirect': time_since_latest_move
                        }
                        self.next_height = floor.height
                        self.log(f'{self.name} send to passengers lift_msg_queue {redirect} from move')
                        PASSENGERS.lift_msg_queue.put_nowait(redirect)
                        triggered = False
                        await asyncio.sleep(0)

                        # reassign unassigned passengers
                        if new_source != prev_floor.name and unassigned_passengers.count_passengers() > 0:
                            self.log(f'{self.name} attempt to reassign for {unassigned_passengers.df.index}')
                            PASSENGERS.reassignment_trigger.put_nowait((prev_floor.name, unassigned_passengers.df.index))
                            # PASSENGERS.reassign_unassigned(floor.name, unassigned_passengers.df.index)

                        # update timer
                        time_to_move = self.calc_time_to_move_while_moving(moving_status, new_source)
                        time_to_arrive = datetime.now() + timedelta(seconds=time_to_move)
                        self.detail_log(f"{self.name} after redirect schedule to arrive in {round(time_to_move, 2)}")
                        continue
                self.log(f'{self.name} no redirect')
                PASSENGERS.lift_msg_queue.put_nowait(redirect)
                triggered = False
                await asyncio.sleep(0)
                
                # update timer
                time_to_move = (time_to_arrive - datetime.now()).total_seconds()
                self.detail_log(f"{self.name} no redirection; schedule to arrive in {round(time_to_move, 2)}")
        except asyncio.TimeoutError:
            self.log(f'{self.name} redirect calc loop timeout')
            # does it ever enter here
            if triggered:
                PASSENGERS.lift_msg_queue.put_nowait(False)
                self.log('lift_msg_queue to release arrival queue')
            await asyncio.sleep(0)
            print_st(f"{self.name} reaches {floor.name}")
            self.log(f"{self.name}: reached {floor.name} at height {floor.height}")
            self.dir = self.next_dir
            self.log(f"{self.name}: latest dir {self.dir}")
            
            self.floor = floor.name
            self.height = floor.height
            self.passengers.update_passenger_floor(floor)
            PASSENGERS.update_lift_passenger_floor(self, floor)
            self.redirect_state = False

        
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
            self.set_stationed()
        self.log(f"{self.name}: Start move from {current_floor.name} height {current_floor.height} at dir {self.dir}")

        import time
        time.sleep(time_to_move)

        self.log(f"{self.name}: reached {floor.name} at height {floor.height}")
        # if self.floor == floor.name:
        #     single_floor_dir = self.find_single_passenger_floor()
        #     if single_floor_dir is not None:
        #         self.dir = single_floor_dir
        #         self.next_dir = 'S'
        #         self.log(f"{self.name}: lone floor directed to {self.dir}")
        
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
            source=source_floor,
            target=target_floor.name,
            lift_spec=self.model
        )
        return moving_status.calc_state(time_elapsed)
    
    def get_moving_status_after_redirect(self, time_elapsed, moving_status, target_floor):
        return moving_status.calc_status(target_floor.height, time_elapsed)

    def get_moving_status_in_loop(self, time_elapsed, target_floor):
        if self.redirect_state == False:
            h, d, v  = self.get_moving_status_from_floor(time_elapsed, self.floor_move_state['start_move_floor'], target_floor)
        else:
            h, d, v = self.get_moving_status_after_redirect(time_elapsed, self.redirect_state['moving_status'], target_floor)
        return CalcAccelModelMovingStatus(h, d, v, self.model)

    def get_moving_status(self, time):
        if self.redirect_state == False:
            time_elapsed = (time-self.floor_move_state['start_move_time']).total_seconds()
            target_floor = FLOOR_LIST.get_floor(self.floor_move_state['target_floor'])
        else:
            time_elapsed = (time-self.redirect_state['time_of_redirect']).total_seconds()
            target_floor = FLOOR_LIST.get_floor(self.redirect_state['target_floor'])
        return self.get_moving_status_in_loop(time_elapsed, target_floor)
    
    def get_reaching_time(self, time, proposed_target_height):
        if self.loading_state is not False:
            current_height = FLOOR_LIST.get_floor(self.floor).height
            loading_time = self.precalc_loading_time(offboarding_mode='arrived', onboarding_mode='earliest')
            time_to_move = self.model.calc_time(abs(proposed_target_height - current_height))
            time_to_load = loading_time - (time - self.loading_state['start_load_time']).total_seconds()
            return time_to_load + time_to_move
        moving_status = self.get_moving_status(time)
        if self.dir == 'S':
            return moving_status.calc_time(proposed_target_height)
        elif moving_status.get_stoppability(proposed_target_height):
            return moving_status.calc_time(proposed_target_height)
        else:
            return None

    def calc_time_to_move_from_floor(self, time_elapsed, source_floor, target_floor, proposed_floor):
        assert self.model.model_type == "accel"

        height, direction, velocity = self.get_moving_status_from_floor(time_elapsed, source_floor, target_floor)

        from src.metrics.CalcAccelModelMovingStatus import CalcAccelModelMovingStatus
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
        if not self.is_stationed():
            self.check_to_turn_back()
            lift_targets = self.passengers.passenger_target_scan().rename(
                columns={'target': 'lift_target'}
            )
            passengers_in_wait = PASSENGERS.filter_by_status_waiting() \
                .filter_by_lift_assigned_not_to_other_only(self)
            waiting_targets = passengers_in_wait.passenger_source_scan().rename(
                columns={'source': 'lift_target'}
            )
            overall_targets = pd.concat([lift_targets, waiting_targets])
            return self.find_next_lift_target(overall_targets)
        else:
            passengers_in_wait = PASSENGERS.filter_by_status_waiting() \
                .filter_by_lift_assigned_not_to_other_only(self)
            targets = passengers_in_wait.passenger_source_scan().rename(
                columns={'source': 'lift_target'}
            )
            nearest_floor = self.find_nearest_floor(targets)
            if nearest_floor is None:
                return None
            if nearest_floor >= self.floor:
                self.dir = 'U'
            else:
                self.dir = 'D'
            self.next_dir = targets.loc[targets.lift_target == nearest_floor, 'dir']
            return nearest_floor
    
    def precalc_next_target_after_loading(self):
        lift_targets = self.passengers.passenger_target_scan().rename(
            columns={'target': 'lift_target'}
        )
        lift_targets = lift_targets.loc[lift_targets.lift_target != self.floor,:]
        passengers_to_board_index = PASSENGERS.df.index.isin(self.precalc_num_to_onboard('earliest', return_index=True))
        passengers_to_board = PassengerList(PASSENGERS.df.loc[passengers_to_board_index, :])
        passengers_to_board_targets = passengers_to_board.passenger_target_scan().rename(
            columns={'target': 'lift_target'}
        )
        passengers_in_wait = PassengerList(
            PASSENGERS.df.loc[(PASSENGERS.df.status == 'Waiting') & (~ passengers_to_board_index), :]
        )
        waiting_targets = passengers_in_wait.passenger_source_scan().rename(
            columns={'source': 'lift_target'}
        )
        overall_targets = pd.concat([lift_targets, passengers_to_board_targets, waiting_targets])
        return self.find_next_lift_target(overall_targets)
    
    def check_to_turn_back(self):
        if self.is_stationed():
            return
        furthest_target, furthest_dir = self.find_furthest_target_dir()
        if self.floor == furthest_target and self.dir != furthest_dir:
            self.dir = furthest_dir
            self.log(f"{self.name}: maximal floor turn back to {self.dir}")
        
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

    def find_nearest_floor(self, targets):
        if targets.shape[0] == 0:
            return None
        
        floor_heights = {f:FLOOR_LIST.get_floor(f).height for f in targets.lift_target}
        floor_dist = {f:abs(self.height - floor_heights[f]) for f in floor_heights}
        return sorted(floor_dist.items(), key=lambda x: x[1])[0][0]
        
    def find_furthest_target_dir(self, remove_extremes=False):
        """
        baseline for lift target algorithm
        attends to the most immediate request
        """
        lift_targets = self.passengers.passenger_target_scan().rename(
            columns={'target': 'lift_target'}
        )
        if remove_extremes:
            to_exclude = (
                (lift_targets.lift_target == max(FLOOR_LIST.list_floors())) & (lift_targets.dir == 'U')
            ) | (
                (lift_targets.lift_target == min(FLOOR_LIST.list_floors())) & (lift_targets.dir == 'D')
            )
            lift_targets = lift_targets.loc[~to_exclude,:]
        passengers_in_wait = PASSENGERS.filter_by_status_waiting().filter_by_lift_assigned_not_to_other_only(self)
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
                current_target.height >= proposed_target.height
            ) and (
                proposed_target.height > current_floor.height
            )
        elif dir == 'D':
            return (
                current_target.height < current_floor.height
            ) and (
                current_target.height <= proposed_target.height
            ) and (
                proposed_target.height < current_floor.height
            )
        return False
    
    def update_next_dir(self, target_floor):
        if target_floor is None:
            self.set_stationed()
            return None
        if not self.is_stationed():
            furthest_floor, furthest_dir = self.find_furthest_target_dir(remove_extremes=True)
            if furthest_floor == target_floor and furthest_dir != self.dir:
                self.next_dir = 'D' if self.dir == 'U' else 'U'
            else:
                self.next_dir = self.dir
    
    def assign_passengers(self, target_floor, assign_multi=True):
        if target_floor is None:
            return
        limit = self.capacity - self.get_total_assigned()
        # nothing more to assign
        if limit <= 0:
            return
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
        self.detail_log(f"{self.name}:  assignment_list {assignment_list.df.loc[:,['status', 'lift', 'current', 'dir', 'source', 'target']]}"
              f"target floor {target_floor} lift next dir {self.next_dir} which has passengers {floor.passengers.df.index.tolist()}")
        PASSENGERS.assign_lift_for_selection(self, assignment_list)
        self.log(f'assigning {self.name} {assignment_list.df.index.tolist()} for {floor.name} which has {floor.passengers.df.index.tolist()}')
        floor.passengers.assign_lift_for_selection(self, assignment_list)

    def unassign_passengers(self, prev_target_floor, prev_next_dir):
        if prev_target_floor is None:
            return None
        prev_floor = FLOOR_LIST.get_floor(prev_target_floor)
        to_unassign = PASSENGERS \
            .filter_by_status_waiting() \
            .filter_by_floor(FLOOR_LIST.get_floor(prev_target_floor)) \
            .filter_by_direction(prev_next_dir) \
            .filter_by_lift_assigned(self)
        PASSENGERS.unassign_lift_for_selection(self, to_unassign)
        prev_floor.passengers.unassign_lift_for_selection(self, to_unassign)

    def get_total_assigned(self):
        non_arrived = PASSENGERS.df.loc[PASSENGERS.df.status != 'Arrived', :]
        return (non_arrived.lift == self.name).sum()
    
    async def lift_baseline_operation(self):
        """
        baseline operation
        """
        self.log(f'{self.name} start baseline operation')
        print(f'{self.name} start baseline operation')
        await asyncio.sleep(0)
        next_target = self.next_baseline_target()
        self.update_next_dir(next_target)
        if next_target is not None:
            print(f'{self.name} lift new target {next_target} next direction {self.next_dir}')
            self.log(f'{self.name} lift new target {next_target} next direction {self.next_dir}')
        self.assign_passengers(next_target, assign_multi=True)
        # print('debug passenger assignment')
        # PASSENGERS.pprint_passenger_status(FLOOR_LIST, ordering_type='source')
        while True:
            if next_target is not None:
                # baseline allows multi assignment after floor is chosen
                print_st(f'{self.name} moving to target {next_target}')
                next_floor = FLOOR_LIST.get_floor(next_target)
                await self.move(next_floor)
                print(f'{self.name} lift moved to target {self.floor} facing {self.dir}')
                await self.loading()
                for lift in PASSENGERS.tracking_lifts:                
                    print(f'{lift.name} facing {lift.dir} after loading at {lift.floor}, lift passengers:',
                          ', '.join([str(i) for i in lift.passengers.df.index.values]))
                self.print_overall_stats()
                await asyncio.sleep(0)
                next_target = self.next_baseline_target()
                self.log(f'{self.name} lift new target {next_target}')
                self.update_next_dir(next_target)        
                print(f'{self.name} lift new target {next_target} next direction {self.next_dir}')
                self.log(f'{self.name} lift next direction {self.next_dir}')
                self.assign_passengers(next_target, assign_multi=True)
                # print('debug passenger assignment')
                # PASSENGERS.pprint_passenger_status(FLOOR_LIST, ordering_type='source')
            else:
                self.log(f"{self.name} setting stationed")
                print_st(f"{self.name} stationed at {self.floor}")
                self.set_stationed()
                await asyncio.sleep(0)
                # to catch passenger arrivals instead of always running
                arrival_task = asyncio.create_task(self.arrival_queue.get())
                reassignment_task = asyncio.create_task(self.reassignment_queue.get())
                to_wait_for = [arrival_task, reassignment_task]
                self.log(f"{self.name} spending arrivals while stationed")
                done, pending = await asyncio.wait(to_wait_for, return_when=asyncio.FIRST_COMPLETED)
                rcv_msg = done.pop().result()
                self.log(f'{self.name} while stationed received queue with {rcv_msg}')
                is_reassignment = False
                if rcv_msg[0] == 'reassign':
                    is_reassignment = True
                    __, new_source, _, new_dir = rcv_msg
                else:
                    new_source, _, new_dir = rcv_msg
                self.log(f'{self.name} evaluating while stationed {new_source, _, new_dir}')
                next_target = self.next_baseline_target()
                self.log(f'{self.name} lift new target {next_target}')
                self.update_next_dir(next_target)
                print(f'{self.name} lift new target {next_target} next direction {self.next_dir}')
                self.log(f'{self.name} lift next direction {self.next_dir}')
                self.assign_passengers(next_target, assign_multi=True)
                
                self.log(f'{self.name} send to passengers lift_msg_queue True from lift_baseline_operation')
                if is_reassignment:
                    PASSENGERS.reassignment_rsp_queue.put_nowait(True)
                else:
                    PASSENGERS.lift_msg_queue.put_nowait(True)
                await asyncio.sleep(0)
                for t in pending:
                    t.cancel()
                # print('debug passenger assignment')
                # PASSENGERS.pprint_passenger_status(FLOOR_LIST, ordering_type='source')

    async def loading(self, print_lift_stats = False, print_passenger_stats=False):
        loading_start_time = datetime.now()
        self.loading_state = {
            'stopping_floor': self.floor,
            'start_load_time': loading_start_time,
        }
        self.loading_state['current_target'] = self.precalc_next_target_after_loading()
        await self.offboard_arrived()
        await self.onboard_earliest_arrival()
        PASSENGERS.update_passenger_metrics(print_passenger_stats, FLOOR_LIST)
        if print_lift_stats:
            self.pprint_current_passengers()
        self.loading_state = False

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

    def print_overall_stats(self):
        print('overall stats', PASSENGERS.df.groupby(['status', 'lift']).size().sort_index(level='status'))
