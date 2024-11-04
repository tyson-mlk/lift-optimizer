import uuid
from datetime import datetime

class Passenger:
    def __init__(self, source, target, trip_start_time = datetime.now()):
        self.id = uuid.uuid1()
        self.source = source
        self.current = source
        self.target = target
        self.dir = self.calculate_direction()
        self.trip_start = trip_start_time
        self.status = 'Waiting'
        self.lift = 'Unassigned'

    def calculate_direction(self):
        if self.target > self.source:
            return 'U'
        elif self.target < self.source:
            return 'D'
        else:
            raise ValueError('problem calculating passenger direction')
