import pandas as pd
from datetime import datetime

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
        'travel_time': 'float64',
        'waiting_time': 'float64',
        'time_on_lift': 'float64'
    }

    def __init__(self, passenger_list_df = None):
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
                        else -1,
                    passenger.waiting_time
                        if 'travel_time' in passenger.__dict__.keys()
                        else -1,
                    passenger.time_on_lift
                        if 'travel_time' in passenger.__dict__.keys()
                        else -1
                ]
            ],
            columns=PassengerList.schema,
            index=[passenger.id],
        ).astype(
            PassengerList.schema
        )
    
    def count_passengers(self) -> int:
        return self.df.shape[0]

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

    def add_passenger_list(self, passenger_df: pd.DataFrame):
        self.df = pd.concat([self.df, passenger_df])

    def passenger_arrival(self, passenger: Passenger):
        passenger_df = PassengerList.passenger_to_df(passenger)
        self.add_passenger_list(passenger_df)
        
        from base.FloorList import FLOOR_LIST
        floor = FLOOR_LIST.get_floor(passenger.source)
        floor.passengers.add_passenger_list(passenger_df)

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
    
    def assign_lift(self, lift):
        from base.Lift import Lift

        assert type(lift) is Lift
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
    
    def update_passenger_metrics(self):
        from metrics.TimeMetrics import calculate_all_metrics

        self.df = calculate_all_metrics(self).df

PASSENGERS = PassengerList()
