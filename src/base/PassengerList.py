import pandas as pd
from datetime import datetime
from logging import INFO, DEBUG
from asyncio import Queue

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

    def __init__(self, passenger_list_df = None, p_list_name = None, lift_tracking = False):
        self.name = p_list_name
        if p_list_name is not None:
            logger = get_logger(p_list_name, self.__class__.__name__, INFO)
            self.log = lambda msg: logger.info(msg)
            self.log(f"{p_list_name}: init")
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
        if lift_tracking:
            self.arrival_queue = Queue()

    def __del__(self):
        self.log(f"{self.name}: destruct")

    async def __aexit__(self, *excinfo):
        if 'arrival_queue' in self.__dict__.keys():
            await self.arrival_queue.join()


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
    
    def register_arrivals(self, passenger):
        msg = passenger.source, passenger.target, passenger.dir
        self.arrival_queue.put_nowait(msg)
    
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
        self.update_boarding_time(passengers)

    def update_boarding_time(self, passengers):
        self.df.loc[passengers.df.index, 'board_time'] = datetime.now()

    def update_arrival(self, passengers):
        self.df.loc[passengers.df.index, 'status'] = 'Arrived'
        self.df.loc[passengers.df.index, 'dest_arrival_time'] = datetime.now()
        self.log(
            f"{self.name}: completed {passengers.count_passengers()};"
            f"count is {self.count_traveling_passengers()}"
        )

    def add_passenger_list(self, passenger_df: pd.DataFrame):
        self.df = pd.concat([self.df, passenger_df])

    def passenger_arrival(self, passenger: Passenger):
        passenger_df = PassengerList.passenger_to_df(passenger)
        self.add_passenger_list(passenger_df)
        self.log(f"{self.name}: 1 new arrival; count is {self.count_traveling_passengers()}")
        
        from base.FloorList import FLOOR_LIST
        floor = FLOOR_LIST.get_floor(passenger.source)
        floor.passengers.add_passenger_list(passenger_df)
        floor.log(f"{floor.name}: 1 new arrival; count is {floor.passengers.count_passengers()}")

        self.register_arrivals(passenger)

    def passenger_list_arrival(self, passengers):
        passenger_df = passengers.df
        self.add_passenger_list(passenger_df)
        self.log(
            f"{self.name}: {passengers.count_passengers()} new arrival;"
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

    # to init test
    def filter_by_lift_assigned(self, lift_name):
        "filters passengers to those assigned to a lift"
        def lift_filter_condition(assignment_condition, lift_name):
            return lift_name == assignment_condition or lift_name in assignment_condition
        filter_condition = self.df.loc[:,'lift'].apply(lambda x: lift_filter_condition(x, lift_name))
        return PassengerList(self.df.loc[filter_condition, :])

    def filter_by_lift_unassigned(self):
        "filters passengers to those not assigned to a lift"
        return PassengerList(self.df.loc[self.df.lift == 'Unassigned', :])
    
    # to init test
    def assign_lift(self, lift, allow_multi_assignment=True):
        from base.Lift import Lift

        assert type(lift) is Lift
        if allow_multi_assignment:
            def append_lift(existing_assignment, lift_name):
                if type(existing_assignment) is list:
                    return existing_assignment + [lift_name]
                else:
                    return [existing_assignment] + [lift_name]
            self.df.loc[self.df.lift != 'Unassigned', 'lift'].apply(lambda x: append_lift(x, lift.name))
            self.df.loc[self.df.lift == 'Unassigned', 'lift'] = lift.name
        else:
            self.df.loc[:, 'lift'] = lift.name
    
    def assign_lift_for_floor(self, lift, floor):
        from base.Lift import Lift

        assert type(lift) is Lift
        assert type(floor) is Floor
        self.df.loc[self.df.source==floor.name, 'lift'] = lift.name
    
    def assign_lift_for_selection(self, lift, passenger_list):
        from base.Lift import Lift

        assert type(lift) is Lift
        assert type(passenger_list) is PassengerList
        self.df.loc[passenger_list.df.index, 'lift'] = lift.name

    def update_passenger_floor(self, floor):
        self.df.loc[:, 'current'] = floor.name

    def update_lift_passenger_floor(self, lift, floor):
        self.df.loc[self.df.lift==lift.name, 'current'] = floor.name

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
        # TODO: floor height ordering to work differently for source, target and current
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


PASSENGERS = PassengerList(p_list_name='all passengers', lift_tracking=True)
