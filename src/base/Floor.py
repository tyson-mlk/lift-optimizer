class Floor:
    def __init__(self, floor, height) -> None:
        self.floor = floor
        self.height = height

        from base.PassengerList import PassengerList
        self.passengers: PassengerList = PassengerList()

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
        self.passengers.remove_all_passengers()

    def onboard_all(self):
        self.reset_passenger_counter()

    # to test
    def onboard_selected(self, passenger_list):
        self.passengers.complement_passenger_list(passenger_list)

    # to test
    def random_select_passengers(self, capacity, passenger_count):
        return self.passengers.sample_passengers(n=capacity-passenger_count)
    
    def select_passengers_by_earliest_arrival(self, capacity, passenger_count):
        num_to_board = capacity - passenger_count
        return self.passengers.df.sort_values('trip_start_time').head(num_to_board)
