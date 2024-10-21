import pandas as pd
from datetime import datetime

from base.Passenger import Passenger
from base.Floor import Floor, FLOOR_LIST

class PassengerList:
    schema = {
        'id': str,
        'source': str,
        'target': str,
        'dir': str,
        'trip_start_time': 'datetime64[ns]',
        'board_time': 'datetime64[ns]',
        'dest_arrival_time': 'datetime64[ns]'
    }

    def __init__(self, passenger_list = None):
        if passenger_list is not None:
            self.df: pd.DataFrameType = pd.DataFrame(
                passenger_list,
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
                    passenger.id,
                    passenger.source,
                    passenger.target,
                    passenger.dir,
                    passenger.trip_start,
                    passenger.board_time
                        if 'board_time' in passenger.__dict__.keys()
                        else None,
                    passenger.dest_arrival_time
                        if 'dest_arrival_time' in passenger.__dict__.keys()
                        else None
                ]
            ],
            columns=PassengerList.schema
        ).astype(
            PassengerList.schema
        )
    
    def count_passengers(self) -> int:
        return self.df.shape[0]

    def bulk_add_passengers(self, passengers):
        self.df = pd.concat([
            self.df,
            passengers.df
        ])

    def remove_passengers(self):
        self.df = self.df.loc[[],:]

    def add_passenger_list(self, passenger_df: pd.DataFrame):
        self.df = pd.concat([self.df, passenger_df])

    def passenger_arrival(self, passenger: Passenger):
        # assert target_floor in FLOORS
        passenger_df = PassengerList.passenger_to_df(passenger)
        self.add_passenger_list(passenger_df)
        floor = FLOOR_LIST.get_floor(passenger.source)
        floor.passengers.add_passenger_list(passenger_df)

    def complement_passenger_list(self, passenger_list):
        self.df = self.df.loc[
            self.df.index.difference(passenger_list.df.index), :
        ]

    def sample_passengers(self, n) -> pd.DataFrame:
        return self.df.sample(n)
    
    def filter_by_floor(self, floor: Floor) -> pd.DataFrame:
        "filters passengers to those on a floor"
        return self.df.loc[self.df.source_floor == floor.floor, :]
    
    def passenger_request_scan(self) -> pd.DataFrame:
        "scan the floor for all passenger requests"
        return self.df.loc[:,['source_floor', 'dir']].drop_duplicates()

PASSENGERS = PassengerList()
