from LiftFloor import FLOORS
from Passenger import Passenger
from Lift import Lift, LIFT_CAPACITY
from random import sample

class FloorPassengers:
    def __init__(self, floor) -> None:
        assert floor in FLOORS

        self.floor = floor
        self.passengers = []
        self.target = {
            target_floor:0 
            for target_floor in FLOORS
        }

    @property
    def floor(self):
        return self._floor
    
    def arrival(self, passengers: list[Passenger]):
        # TODO: to log arrival time of passengers
        for passenger in passengers:
            self.target[passenger.target] += 1
        self.passengers.extend(passengers)

    # TODO: master module to let lifts signal what are eligible passengers
    def board(self, eligible_floors: list[str], lift: Lift):
        passenger_index = list(zip(range(len(self.passengers)), self.passengers))
        eligible_index = [item[0] for item in passenger_index if item[1].target in eligible_floors]
        
        # under-capacity lift
        if len(eligible_index) + lift.passenger_count > LIFT_CAPACITY:
            eligible_index = sample( eligible_index, LIFT_CAPACITY - lift.passenger_count)
        eligible_passengers = self.passengers[eligible_index]

        # TODO: to log boarding time of passengers
        lift.onboard(eligible_passengers)

        for passenger in eligible_passengers:
            self.target[passenger.target] -= 1
        ineligible_index = [i for i in range(len(self.passengers)) if i not in eligible_index]
        self.passengers = self.passengers[ineligible_index]
