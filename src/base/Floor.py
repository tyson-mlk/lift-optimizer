from numpy.random import choice
import pandas as pd
from Lift import LIFT_CAPACITY, Lift
from Passenger import Passenger
from Passengers import Passengers, PASSENGERS

FLOORS = list(str(i).zfill(3) for i in range(20))
FLOOR_HEIGHTS = {str(i).zfill(3):i for i in range(20)}

class Floor:
    def __init__(self, floor) -> None:
        assert floor in FLOORS

        self.floor = floor
        self.height = FLOOR_HEIGHTS[self.floor]
        self.passengers: Passengers = Passengers()

    @property
    def floor(self):
        return self._floor

    # @property
    # def passenger_target_counter(self):
    #     return self._passenger_target_counter
    
    def get_floor_count(self):
        return self.passengers.passenger_list.shape[0]
    
    def passegner_arrival(self, target_floor, start_time):
        assert target_floor in FLOORS
        # self.passenger_target_counter[target_floor] += 1
        passenger = Passenger(self.floor, target_floor, start_time)
        PASSENGERS.passenger_arrival(passenger)
        self.passengers.passenger_arrival(passenger)

    def reset_passenger_counter(self):
        self.passengers.passenger_list = self.passengers.passenger_list.loc[[],:]

    def onboard_all(self):
        self.reset_passenger_counter()

    def onboard_selected(self, selection):
        self.passengers.passenger_list = self.passengers.passenger_list.loc[
            self.passengers.index.difference(selection.index), :
        ]

    def random_select_passengers(self, lift: Lift):
        return self.passengers.passenger_list.sample(n=LIFT_CAPACITY-lift.passenger_count)
