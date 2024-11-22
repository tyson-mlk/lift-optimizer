from logging import INFO, DEBUG

from utils.Logging import get_logger

class Floor:
    def __init__(self, floorname, height) -> None:
        self.name = floorname
        self.height = height

        from base.PassengerList import PassengerList
        self.passengers: PassengerList = PassengerList()

    def init_logger(self):
        logger = get_logger(self.name, self.__class__.__name__, INFO)
        self.log = lambda msg: logger.info(msg)

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, new_name):
        self._name = new_name
    
    def get_floor_count(self):
        return self.passengers.count_passengers()
    
    def get_floor_passenger_count_with_dir(self, direction):
        return self.passengers.filter_by_direction(direction).count_passengers()

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
    
    def select_passengers_with_dir_by_earliest_arrival(self, lift_dir, capacity, passenger_count):
        num_to_board = capacity - passenger_count
        passenger_df = self.passengers.df
        print('DEBUG onboard selection', passenger_df.loc[passenger_df.dir == lift_dir, :] \
            .sort_values('trip_start_time').head(num_to_board))
        return passenger_df.loc[passenger_df.dir == lift_dir, :] \
            .sort_values('trip_start_time').head(num_to_board)
