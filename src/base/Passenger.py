import sys

sys.path.append('..')

from utils.PassengerMetric import PassengerMetric
import uuid

class Passenger:
    def __init__(self, source, target, trip_start_time):
        self.id = uuid.uuid1()
        self.source = source
        self.target = target
        self.floor = source
        self.trip_start = trip_start_time
        self.lift = None
        # self.measurement = None

    @property
    def floor(self):
        return self._floor
    
    @property
    def lift(self):
        return self._lift
    
    @floor.setter
    def floor(self, new_floor):
        self._floor = new_floor

    @lift.setter
    def lift(self, new_lift):
        if new_lift.has_capacity():
            self._lift = new_lift

    # def start_journey(self, start_time):
    #     self.measurement = PassengerMetric(start_time)

    # def update_lift_arrival(self, board_time):
    #     self.measurement.update_lift_arrival(board_time)

    # def update_dest_arrival(self, arrival_time):
    #     self.measurement.update_dest_arrival(arrival_time)
