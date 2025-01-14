import pandas as pd
from datetime import datetime
from logging import INFO, DEBUG
import asyncio

from utils.Logging import get_logger
from base.Passenger import Passenger
from base.Floor import Floor

class PassengerList:
    schema = {
        'source': str,
        'current': str,
        'target': str,
        'dir': str,
        'status': str,
        'lift': str,
        'trip_start_time': 'datetime64[ns]',
        'board_time': 'datetime64[ns]',
        'dest_arrival_time': 'datetime64[ns]',
        'travel_time': 'Float64',
        'waiting_time': 'Float64',
        'time_on_lift': 'Float64'
    }

    def __init__(self, passenger_list_df = None, p_list_name = None,
                 lift_managing = False, lift_tracking = False):
        self.name = p_list_name
        self.lift_managing = lift_managing
        if p_list_name is not None:
            logger = get_logger(p_list_name, self.__class__.__name__, INFO)
            pa_assignment_logger = get_logger(p_list_name+'_arr_ass', self.__class__.__name__, DEBUG)
            self.log = lambda msg: logger.info(msg)
            self.log(f"{p_list_name}: init")
            self.custom_log = lambda msg: pa_assignment_logger.debug(msg)
        else:
            self.log = lambda *args: None
        if passenger_list_df is not None:
            self.df: pd.DataFrameType = pd.DataFrame(
                passenger_list_df,
                index=passenger_list_df.index,
                columns=PassengerList.schema
            ).astype(
                PassengerList.schema
            )
        else:
            self.df: pd.DataFrameType = pd.DataFrame(
                columns=PassengerList.schema
            ).astype(
                PassengerList.schema
            )
        if lift_managing:
            self.lift_msg_queue = asyncio.Queue()
            self.reassignment_trigger = asyncio.Queue()
            self.reassignment_rsp_queue = asyncio.Queue()
            self.arrival_lock = asyncio.Lock()
            self.tracking_lifts = []

    def __del__(self):
        self.log(f"{self.name}: start destructing")
        if self.lift_managing:
            if self.arrival_lock.locked():
                self.log(f"{self.name}: releasing arrival_lock to destruct")
                self.arrival_lock.release()
            while not self.reassignment_trigger.empty():
                msg = self.reassignment_trigger.get_nowait()
                self.log(f"{self.name}: flushing reassignment_trigger item {msg}")
            while not self.lift_msg_queue.empty():
                msg = self.lift_msg_queue.get_nowait()
                self.log(f"{self.name}: flushing lift_msg_queue item {msg}")
            while not self.reassignment_rsp_queue.empty():
                msg = self.reassignment_rsp_queue.get_nowait()
                self.log(f"{self.name}: flushing reassignment_rsp_queue item {msg}")
        self.log(f"{self.name}: destruction complete")


    @classmethod
    def passenger_to_df(cls, passenger: Passenger):
        return pd.DataFrame(
            [
                [
                    passenger.source,
                    passenger.current,
                    passenger.target,
                    passenger.dir,
                    passenger.status,
                    passenger.lift,
                    passenger.trip_start,
                    passenger.board_time
                        if 'board_time' in passenger.__dict__.keys()
                        else None,
                    passenger.dest_arrival_time
                        if 'dest_arrival_time' in passenger.__dict__.keys()
                        else None,
                    passenger.travel_time
                        if 'travel_time' in passenger.__dict__.keys()
                        else pd.NA,
                    passenger.waiting_time
                        if 'travel_time' in passenger.__dict__.keys()
                        else pd.NA,
                    passenger.time_on_lift
                        if 'travel_time' in passenger.__dict__.keys()
                        else pd.NA
                ]
            ],
            columns=PassengerList.schema,
            index=[passenger.id],
        ).astype(
            PassengerList.schema
        )
    
    def get_passenger_by_id(self, passenger_id):
        return self.df.loc[passenger_id,:]
    
    async def search_lifts_to_queue_passenger(self, passenger_id, source, target, dir):
        msg = source, target, dir
        search_redirect_lift = self.lift_search_redirect_gen(source, dir)
        for next_lift in iter(search_redirect_lift):
            if self.df.loc[passenger_id, 'lift'] != 'Unassigned':
                self.log(f"passenger {passenger_id} assigned; stop search")
                break
            next_lift.log(f'{next_lift.name} from {next_lift.floor} evaluating for {msg}')
            next_lift.arrival_queue.put_nowait(msg)
            self.log(f"evaluating {next_lift.name} for {passenger_id}")
            assigned = await self.lift_msg_queue.get()
            self.log(f"evaluation {next_lift.name} for {passenger_id} is {assigned}")

    async def reassign_to_stationary_lifts(self, lifts_for_reassignment, passenger_ids):
        """assigns one passenger per stationary lift"""
        lift = next(lifts_for_reassignment, None)
        if lift is None:
            self.log("no stationary lift for reassignment")
            return
        remaining_passenger_ids = passenger_ids
        while lift is not None:
            self.log(f"calculating reassignment of lift {lift.name} for passengers {passenger_ids}")
            remaining_capacity = lift.capacity - lift.passenger_count
            if remaining_capacity >= len(passenger_ids):
                to_assign = passenger_ids
            else:
                to_assign = passenger_ids[:remaining_capacity]
            msg = tuple(
                ['reassign'] +
                self.df.reset_index() \
                .loc[to_assign, ['source', 'target', 'dir']] \
                .drop_duplicates() \
                .values[0].tolist()
            )
            if lift.is_stationed():
                lift.reassignment_queue.put_nowait(msg)
                self.log(f"reassignment evaluating {lift.name} for {passenger_ids}")
                assigned = await self.reassignment_rsp_queue.get()
                self.log(f"reassignment evaluation {lift.name} for {passenger_ids} is {assigned}")
                if assigned:
                    self.log(f"reassigned {to_assign} to {lift.name}")
                    remaining_passenger_ids = [i for i in remaining_passenger_ids if i not in to_assign]
                    if len(remaining_passenger_ids) == 0:
                        return
            lift = next(lifts_for_reassignment, None)

    def register_lift(self, lift):
        assert hasattr(self, 'tracking_lifts')
        self.tracking_lifts += [lift]

    def lift_search_redirect_gen(self, arrival_source, arrival_dir):
        time = datetime.now()
        lift_order = {}

        from base.FloorList import FLOOR_LIST
        target_height = FLOOR_LIST.get_floor(arrival_source).height
        for lift in PASSENGERS.tracking_lifts:
            if (lift.dir == arrival_dir or lift.dir == 'S'):
                time_to_reach = lift.get_reaching_time(time, target_height)
                self.custom_log(f'lift_search_redirect_gen {lift.name} time_to_reach {time_to_reach}')
                if time_to_reach is not None:
                    lift_order[lift] = time_to_reach
        search_order = sorted(lift_order.items(), key=lambda x: x[1])
        self.custom_log(f'search order {[[item[0].name, item[1]] for item in search_order]}')
        for sorted_lift in search_order:
            yield sorted_lift[0]

    def lift_search_reassign_stationary_gen(self, arrival_source):
        time = datetime.now()
        lift_order = {}

        from base.FloorList import FLOOR_LIST
        target_height = FLOOR_LIST.get_floor(arrival_source).height
        for lift in PASSENGERS.tracking_lifts:
            if lift.dir != 'S':
                continue
            time_to_reach = lift.get_reaching_time(time, target_height)
            if time_to_reach is not None:
                lift_order[lift] = time_to_reach
        search_order = sorted(lift_order.items(), key=lambda x: x[1])
        self.custom_log(f'search order {[[item[0].name, item[1]] for item in search_order]}')
        for sorted_lift in search_order:
            yield sorted_lift[0]
    
    def count_passengers(self) -> int:
        return self.df.shape[0]
    
    def count_traveling_passengers(self) -> int:
        return (self.df.status != 'Arrived').sum()

    def bulk_add_passengers(self, passengers):
        self.df = pd.concat([
            self.df,
            passengers.df
        ], axis=0)

    def remove_all_passengers(self):
        self.df = self.df.loc[[],:]

    def remove_passengers(self, passengers):
        self.complement_passenger_list(passengers)

    def board(self, passengers):
        self.df.loc[passengers.df.index, 'status'] = 'Onboard'
        self.log(f'board: passengers {passengers.df.index.tolist()} boarding')
        self.update_boarding_time(passengers)

    def update_boarding_time(self, passengers):
        self.df.loc[passengers.df.index, 'board_time'] = datetime.now()

    def update_arrival(self, passengers):
        self.df.loc[passengers.df.index, 'status'] = 'Arrived'
        self.df.loc[passengers.df.index, 'dest_arrival_time'] = datetime.now()
        self.log(
            f"{self.name}: {passengers.count_passengers()} passengers {passengers.df.index.tolist()} completed"
            f"count is {self.count_traveling_passengers()}"
        )

    def add_passenger_list(self, passenger_df: pd.DataFrame):
        self.df = pd.concat([self.df, passenger_df])

    async def passenger_arrival(self, passenger: Passenger):
        passenger_df = PassengerList.passenger_to_df(passenger)
        self.add_passenger_list(passenger_df)
        self.log(
            f"{self.name}: passenger {passenger.id} new arrival;"
            f"count is {self.count_traveling_passengers()}"
        )
        
        from base.FloorList import FLOOR_LIST
        floor = FLOOR_LIST.get_floor(passenger.source)
        floor.passengers.add_passenger_list(passenger_df)
        floor.log(f"{floor.name}: 1 new arrival; count is {floor.passengers.count_passengers()}")

        # if not all([i in self.df.index for i in range(1,passenger.id+1)]):
        #     print(list(range(1,passenger.id+1)), self.df.index)
        assert all([i in self.df.index for i in range(1,passenger.id+1)])

        self.log(f'arrival search, attempt to acquire, is locked {self.arrival_lock.locked()}')
        async with self.arrival_lock:
            # flush any previous queue items
            while not self.lift_msg_queue.empty():
                self.lift_msg_queue.get_nowait()
            self.log('arrival search, acquired')
            self.custom_log(f"queuing for arrival of {passenger.id}")
            await self.search_lifts_to_queue_passenger(passenger.id, passenger.source,
                                                       passenger.target, passenger.dir)
        self.log('arrival search, released')

    async def reassignment_listener(self):
        self.log('start reassignment listener')
        while True:
            arrival_source, passenger_ids = await self.reassignment_trigger.get()
            self.log(f'reassignment triggered for {arrival_source, passenger_ids}')
            await self.reassign_unassigned(arrival_source, passenger_ids)
            self.log('reassignment listener loop end')

    async def reassign_unassigned(self, arrival_source, passenger_ids):
        lifts_for_reassignment = self.lift_search_reassign_stationary_gen(arrival_source)
        if not hasattr(lifts_for_reassignment, '__iter__'):
            self.log('invalid type for lifts_for_reassignment')
            return
        await self.reassign_to_stationary_lifts(lifts_for_reassignment, passenger_ids)

    def passenger_list_arrival(self, passengers):
        passenger_df = passengers.df
        self.add_passenger_list(passenger_df)
        self.log(
            f"{self.name}: {passengers.count_passengers()} passengers {passenger_df.index.tolist()} new arrival;"
            f"count is {self.count_traveling_passengers()}"
        )
        
        from base.FloorList import FLOOR_LIST
        for floor_name in passengers.df.source.unique():
            floor = FLOOR_LIST.get_floor(floor_name)
            floor.passengers.add_passenger_list(
                passengers.df.loc[passengers.df.source == floor_name,:]
            )
            floor.log(
                f"{floor.name}: {(passengers.df.source == floor_name).sum()} new arrival;"
                f" count is {floor.passengers.count_passengers()}"
            )

    def complement_passenger_list(self, passenger_list):
        self.df = self.df.loc[
            self.df.index.difference(passenger_list.df.index), :
        ]

    def sample_passengers(self, n) -> pd.DataFrame:
        return self.df.sample(n)

    def filter_by_floor(self, floor: Floor):
        "filters passengers to those on a floor"
        return PassengerList(self.df.loc[self.df.current == floor.name, :])

    def filter_by_destination(self, floor: Floor):
        "filters passengers to those on a floor"
        return PassengerList(self.df.loc[self.df.target == floor.name, :])

    def filter_by_direction(self, direction):
        "filters passengers to those on a floor"
        return PassengerList(self.df.loc[self.df.dir == direction, :])

    def filter_by_lift_assigned(self, lift):
        "filters passengers to those assigned to a lift"
        def lift_filter_condition(assignment_condition, lift_name):
            return lift_name == assignment_condition or lift_name in assignment_condition
        filter_condition = self.df.loc[:,'lift'].apply(lambda x: lift_filter_condition(x, lift.name))
        return PassengerList(self.df.loc[filter_condition, :])

    def filter_by_lift_unassigned(self):
        "filters passengers to those not assigned to a lift"
        return PassengerList(self.df.loc[self.df.lift == 'Unassigned', :])
    
    def filter_by_lift_assigned_not_to_other_only(self, lift):
        """as a signal of availability filters passengers 
        to those assigned to this or not assigned to other lift"""
        def lift_filter_condition(assignment_condition, lift_name):
            return (
                type(assignment_condition) is str and
                (
                    assignment_condition == lift_name or
                    assignment_condition == 'Unassigned'
                )
            ) or (
                type(assignment_condition) is list and
                (
                    lift_name in assignment_condition or
                    len(assignment_condition) == 0
                )
            )
        filter_condition = self.df.loc[:,'lift'].apply(lambda x: lift_filter_condition(x, lift.name))
        return PassengerList(self.df.loc[filter_condition, :])
    
    def filter_dir_for_earliest_arrival(self, dir, n):
        filtered_df = self.df.loc[self.df.dir == dir, :]
        to_select = min(n, filtered_df.shape[0])
        return filtered_df.sort_values('trip_start_time').head(to_select)
    
    def filter_by_earliest_arrival(self, n):
        return PassengerList(self.df.sort_values('trip_start_time').head(n))

    def filter_by_status_waiting(self):
        "filters passengers to those waiting"
        return PassengerList(self.df.loc[self.df.status == 'Waiting', :])
    
    @classmethod
    def append_lift(cls, existing_assignment, lift_name):
        if type(existing_assignment) is list:
            if lift_name in existing_assignment:
                return existing_assignment
            return existing_assignment + [lift_name]
        elif (
            type(existing_assignment) is str and
            len(existing_assignment) > 0 and
            existing_assignment[0] == "[" and
            existing_assignment[-1] == "]"
        ):
            existing_assignment = existing_assignment[1:-1].split(', ')
            existing_assignment = list(map(lambda x: x.replace("'", ""), existing_assignment))
            if lift_name in existing_assignment:
                return existing_assignment
            return existing_assignment + [lift_name]
        elif type(existing_assignment) is str:
            if existing_assignment == 'Unassigned':
                return lift_name
            elif lift_name != existing_assignment:
                return [existing_assignment] + [lift_name]
            else:
                return existing_assignment
    
    def assign_lift(self, lift, assign_multi=True):
        from base.Lift import Lift

        assert type(lift) is Lift
        if assign_multi:
            self.df.loc[(self.df.status == 'Waiting') & (self.df.lift != 'Unassigned'), 'lift'] = \
                self.df.loc[(self.df.status == 'Waiting') & (self.df.lift != 'Unassigned'), 'lift'] \
                .apply(lambda x: PassengerList.append_lift(x, lift.name))
            self.df.loc[(self.df.status == 'Waiting') & (self.df.lift == 'Unassigned'), 'lift'] = lift.name
        else:
            self.df.loc[self.df.status == 'Waiting', 'lift'] = lift.name
    
    def assign_lift_for_floor(self, lift, floor, assign_multi=True):
        from base.Lift import Lift

        assert type(lift) is Lift
        assert type(floor) is Floor
        if assign_multi:
            self.df.loc[(self.df.status == 'Waiting') & (self.df.source==floor.name), 'lift'] = \
                self.df.loc[(self.df.status == 'Waiting') & (self.df.source==floor.name), 'lift'] \
                .apply(lambda x: PassengerList.append_lift(x, lift.name))
        else:
            self.df.loc[(self.df.status == 'Waiting') & (self.df.source==floor.name), 'lift'] = lift.name
    
    def assign_lift_for_selection(self, lift, passenger_list, assign_multi=True):
        from base.Lift import Lift

        assert type(lift) is Lift
        assert type(passenger_list) is PassengerList
        if assign_multi:
            self.df.loc[passenger_list.df.index, 'lift'] = \
                self.df.loc[passenger_list.df.index, 'lift'] \
                .apply(lambda x: PassengerList.append_lift(x, lift.name))
        else:
            self.df.loc[passenger_list.df.index, 'lift'] = lift.name

    def unassign_lift_for_selection(self, lift, passenger_list):
        from base.Lift import Lift

        assert type(lift) is Lift
        assert type(passenger_list) is PassengerList
        def unassign(lift_name, existing_assignment):
            if type(existing_assignment) is str:
                if existing_assignment == lift_name:
                    return "Unassigned"
            elif type(existing_assignment) is list:
                if lift_name in existing_assignment:
                    return [l for l in existing_assignment if l != lift_name]
            return existing_assignment
                
        self.df.loc[passenger_list.df.index, 'lift'] = \
            self.df.loc[passenger_list.df.index, 'lift'].apply(
                lambda x: unassign(lift.name, x)
            )

    def update_passenger_floor(self, floor):
        self.df.loc[:, 'current'] = floor.name

    def update_lift_passenger_floor(self, lift, floor):
        self.df.loc[(self.df.status == 'Onboard') & (self.df.lift==lift.name), 'current'] = floor.name

    def passenger_target_scan(self) -> pd.DataFrame:
        "scan for all passenger target destination"
        return self.df.loc[:,['target', 'dir']].drop_duplicates()

    def passenger_source_scan(self) -> pd.DataFrame:
        "scan for all passenger source floors"
        return self.df.loc[:,['source', 'dir']].drop_duplicates()
    
    def update_passenger_metrics(self, print_passenger_metrics,
                                 floor_list, ordering_type='source'):
        from metrics.TimeMetrics import calculate_all_metrics

        self.df = calculate_all_metrics(self).df
        if print_passenger_metrics:
            self.pprint_passenger_status(floor_list, ordering_type=ordering_type)

    def pprint_passenger_status(self, floor_list, ordering_type='source'):
        def format_trip(df):
            return df.source + " -> " + df.target

        df = self.df.copy()
        assert ordering_type in df.columns

        df['trip'] = format_trip(df)
        df['order'] = df.apply(lambda x: floor_list.floor_height_order(x[ordering_type], x.dir), axis=1)
        
        print( 'All passengers',
            df.loc[:, ['trip', 'status', 'lift', 'order']] \
                .sort_values('order').drop(columns='order')
        )

    def pprint_passenger_details(self, ordering=None):
        def format_trip(df):
            return df.source + " -> " + df.target

        def passenger_time_format(t):
            return t.strftime("%H:%M:%S") if t is not pd.NaT else "NA"

        def format_start_time(df):
            return df.trip_start_time.apply(passenger_time_format)

        def format_board_time(df):
            return df.board_time.apply(passenger_time_format)

        def format_dest_arrival_time(df):
            return df.dest_arrival_time.apply(passenger_time_format)
        
        df = self.df.copy()
        df['trip'] = format_trip(df)
        df['start_time'] = format_start_time(df)
        df['board_time'] = format_board_time(df)
        df['dest_arrival_time'] = format_dest_arrival_time(df)
        df['waiting_time'] = df.waiting_time.round(2)
        df['time_on_lift'] = df.time_on_lift.round(2)
        df['travel_time'] = df.travel_time.round(2)

        print_cols = ['trip', 'status', 'start_time', 'lift', 'board_time', 'current', 'dest_arrival_time',
                      'waiting_time', 'time_on_lift', 'travel_time']
        print('all passengers state')
        if ordering is not None:
            assert ordering in print_cols
            print(df.loc[:, print_cols].sort_values(ordering))
        else:
            print(df.loc[:, print_cols])


PASSENGERS = PassengerList(
    p_list_name='all passengers', lift_managing=True, lift_tracking=True
)
