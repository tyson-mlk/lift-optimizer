from itertools import count
from datetime import datetime

class Passenger:
    _passenger_record = count(1)

    def __init__(self, source, target, trip_start_time = datetime.now()):
        self.id = next(self._passenger_record)
        self.source = source
        self.current = source
        self.target = target
        self.dir = self.calculate_direction()
        self.trip_start = trip_start_time
        self.status = 'Waiting'
        self.lift = 'Unassigned'

    @classmethod
    def passenger_record(cls):
        cls._passenger_record += 1
        return cls._passenger_record

    def calculate_direction(self):
        if self.target > self.source:
            return 'U'
        elif self.target < self.source:
            return 'D'
        else:
            raise ValueError('problem calculating passenger direction')
