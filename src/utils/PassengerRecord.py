from src.base.Passenger import Passenger
from src.base.PassengerList import PassengerList
from src.base.Floor import Floor
from datetime import datetime
import pandas as pd

class PassengerRecord:
    def __init__(self, passengers: PassengerList) -> None:
        self.record = PassengerList.passenger_to_df(passengers)

    def add_to_record(self, passenger: Passenger) -> None:
        pass

    def update_record(self, passengers: PassengerList) -> None:
        pass

    def slice_by_start_time(self, time_start: datetime, time_end: datetime) -> pd.DataFrame:
        pass

    def slice_by_source_lift_floor(self, source_floor: Floor) -> pd.DataFrame:
        pass

    def slice_by_target_lift_floor(self, target_floor: Floor) -> pd.DataFrame:
        pass
