from random import sample

from base.Lift import FLOOR_LIST
from base.Passenger import Passenger
from base.Lift import Lift

class PreBoardPassengers:
    def __init__(self, floor) -> None:
        assert floor in FLOOR_LIST

        self.floor = floor
        self.passengers = []
        self.target = {
            target_floor:0 
            for target_floor in FLOOR_LIST
        }

    @property
    def floor(self):
        return self._floor
    
    def arrival(self, passengers: list[Passenger], start_time):
        # TODO: to log arrival time of passengers
        for passenger in passengers:
            self.target[passenger.target] += 1
            passenger.measurement.start_journey(start_time)
        self.passengers.extend(passengers)

    # TODO: master module to let lifts signal what are eligible passengers
    def board(self, eligible_floors: list[str], lift: Lift, lift_arrival_time):
        passenger_index = list(zip(range(len(self.passengers)), self.passengers))
        eligible_index = [item[0] for item in passenger_index if item[1].target in eligible_floors]
        
        # under-capacity lift
        if len(eligible_index) + lift.passenger_count > lift.capacity:
            eligible_index = sample( eligible_index, lift.capacity - lift.passenger_count)
        eligible_passengers = self.passengers[eligible_index]

        # TODO: to log boarding time of passengers
        for passenger in eligible_passengers:
            passenger.measurement.update_lift_arrival(lift_arrival_time)
        lift.onboard(eligible_passengers)

        for passenger in eligible_passengers:
            self.target[passenger.target] -= 1
        ineligible_index = [i for i in range(len(self.passengers)) if i not in eligible_index]
        self.passengers = self.passengers[ineligible_index]
