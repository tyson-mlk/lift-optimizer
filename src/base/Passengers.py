import pandas as pd
from Floor import Floor
from Passenger import Passenger

class Passengers:
    schema = {
        'id': str,
        'source': str,
        'target': str,
        'dir': str,
        'trip_start_time': 'datetime64[ns]',
        'board_time': 'datetime64[ns]',
        'dest_arrival_time': 'datetime64[ns]'
    }

    def __init__(self):
        self.passenger_list: pd.DataFrameType = pd.DataFrame(
            columns=Passengers.schema
        ).astype(
            Passengers.schema
        )

    @classmethod
    def passenger_to_df(passenger: Passenger):
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
            columns=Passengers.schema
        ).astype(
            Passengers.schema
        )
    
    def count_passengers(self) -> int:
        return self.passenger_list.shape[0]
        
    def passenger_arrival(self, passenger: Passenger):
        passenger_df = Passenger.passenger_to_df(passenger)
        self.passenger_list = pd.concat([self.passenger_list, passenger_df])

    def bulk_add_passengers(self, passengers):
        self.passenger_list = pd.concat([
            self.passenger_list,
            passengers.passenger_list
        ])

    def combine_passenger_list(self, passenger_list):
        return pd.concat([
            self.passenger_list,
            passenger_list
        ])

    def bulk_add_passenger_list(self, passenger_list):
        self.passenger_list = pd.concat([
            self.passenger_list,
            passenger_list
        ])

    def remove_passengers(self):
        self.passenger_list = self.passenger_list.loc[[],:]

    def complement_passenger_list(self, selection):
        self.passenger_list = self.passenger_list.loc[
            self.passenger_list.index.difference(selection.index), :
        ]

    def sample_passengers(self, n) -> pd.DataFrame:
        return self.passenger_list.sample(n)
    
    def filter_by_floor(self, floor: Floor) -> pd.DataFrame:
        "filters passengers to those on a floor"
        return self.passenger_list.loc[self.passenger_list.source_floor == floor.floor, :]
    
    def passenger_request_scan(self) -> pd.DataFrame:
        "scan the floor for all passenger requests"
        return self.passenger_list.loc[:,['source_floor', 'dir']].drop_duplicates()

PASSENGERS = Passengers()
