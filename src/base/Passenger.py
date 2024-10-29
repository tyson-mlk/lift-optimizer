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
        self.lift = None
        # self.measurement = None

    def calculate_direction(self):
        if self.target > self.source:
            return 'U'
        elif self.target < self.source:
            return 'D'
        else:
            raise Exception('problem calculating passenger direction')

    # def start_journey(self, start_time):
    #     self.measurement = PassengerMetric(start_time)

    # def update_lift_arrival(self, board_time):
    #     self.measurement.update_lift_arrival(board_time)

    # def update_dest_arrival(self, arrival_time):
    #     self.measurement.update_dest_arrival(arrival_time)
