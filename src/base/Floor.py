from numpy.random import choice
from Lift import LIFT_CAPACITY, Lift

FLOORS = list(str(i).zfill(3) for i in range(20))
FLOOR_HEIGHTS = {str(i).zfill(3):i for i in range(20)}

class Floor:
    def __init__(self, floor) -> None:
        assert floor in FLOORS

        self.floor = floor
        self.height = FLOOR_HEIGHTS[self.floor]
        self.passenger_target_counter = {
            target_floor:0 
            for target_floor in FLOORS
        }

    @property
    def floor(self):
        return self._floor

    @property
    def passenger_target_counter(self):
        return self._passenger_target_counter
    
    def get_floor_count(self):
        return sum([c for ptc, c in self.passenger_target_counter.items()])
    
    def passenger_targets(self):
        ptc = self.passenger_target_counter()
        return sum([[i] * ptc[i] for i in ptc], [])
    
    def passegner_arrival(self, target_floor):
        assert target_floor in FLOORS
        self.passenger_target_counter[target_floor] += 1

    def reset_passenger_counter(self):
        self.passenger_target_counter = {
            target_floor:0 
            for target_floor in FLOORS
        }

    def onboard_all(self):
        self.reset_passenger_counter()

    def onboard_selected(self, selection):
        for target_floor in selection:
            self.passenger_target_counter[target_floor] -= 1

    def random_select_passengers(self, lift: Lift):
        selection = choice(
            a=sum([[i[0]] * i[1] for i in self.passenger_target_counter.items()], []),
            size=LIFT_CAPACITY-lift.passenger_count,
            replace=False
        )
        return selection
