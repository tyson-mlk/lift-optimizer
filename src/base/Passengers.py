import uuid
import pandas as pd
from numpy import datetime64
from Passenger import Passenger

class Passengers:
    schema = {
        'id': str,
        'source': str,
        'target': str,
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

    def passenger_to_df(passenger: Passenger):
        return pd.DataFrame(
            [
                [
                    passenger.id,
                    passenger.source,
                    passenger.target,
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
        
    def passenger_arrival(self, passenger: Passenger):
        passenger_df = Passenger.passenger_to_df(passenger)
        self.passenger_list = pd.concat([self.passenger_list, passenger_df])

    