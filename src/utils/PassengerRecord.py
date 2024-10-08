import sys

sys.path.append('..')

from base.Passenger import Passenger
from base.LiftFloor import LiftFloor
from datetime import datetime
import pandas as pd

class PassengerRecord:
    ""
    passenger_record_columns = ['id', 'source', 'target', 'start_time', 'board_time', 'arrival_time']

    def __init__(self) -> None:
        self.record = pd.DataFrame([], columns=self.passenger_record_columns)
        pass

    def add_to_record(self, passenger: Passenger) -> None:
        pass

    def update_record(self, passengers: list[Passenger]) -> None:
        pass

    def slice_by_start_time(self, time_start: datetime, time_end: datetime) -> pd.DataFrame:
        pass

    def slice_by_source_lift_floor(self, floor: LiftFloor) -> pd.DataFrame:
        pass

    def slice_by_target_lift_floor(self, floor: LiftFloor) -> pd.DataFrame:
        pass