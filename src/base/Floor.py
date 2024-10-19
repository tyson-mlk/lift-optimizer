class Floor:
    def __init__(self, floor, height) -> None:
        # assert floor in FLOOR_LIST
        self.floor = floor
        self.height = height

        from base.Passengers import Passengers
        self.passengers: Passengers = Passengers()

    @property
    def floor(self):
        return self._floor
    
    @floor.setter
    def floor(self, new_floor):
        self._floor = new_floor

    # @property
    # def passenger_target_counter(self):
    #     return self._passenger_target_counter
    
    def get_floor_count(self):
        return self.passengers.count_passengers()

    def reset_passenger_counter(self):
        self.passengers.remove_passengers()

    def onboard_all(self):
        self.reset_passenger_counter()

    # untested
    def onboard_selected(self, selection):
        self.passengers.complement_passenger_list(selection)

    # untested
    def random_select_passengers(self, capacity, passenger_count):
        return self.passengers.sample_passengers(n=capacity-passenger_count)
    
    def select_passengers_by_earliest_arrival(self):
        pass

FLOOR_LIST = []
FLOORS = list(str(i).zfill(3) for i in range(20))
MIN_FLOOR = min(FLOORS)
MAX_FLOOR = max(FLOORS)
FLOOR_HEIGHTS = {str(i).zfill(3):i for i in range(20)}
for floor in list(str(i).zfill(3) for i in range(20)):
    FLOOR_LIST.append(Floor(floor, FLOOR_HEIGHTS[floor]))
