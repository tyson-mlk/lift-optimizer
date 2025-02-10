from logging import INFO, DEBUG
from datetime import datetime
from pandas import NaT

from src.utils.Logging import get_logger

class Floor:
    def __init__(self, floorname, height) -> None:
        self.name = floorname
        self.height = height

        from src.base.PassengerList import PassengerList
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

    def onboard_selected(self, passenger_list):
        self.passengers.complement_passenger_list(passenger_list)

    # def random_select_passengers(self, capacity, passenger_count):
    #     return self.passengers.sample_passengers(n=capacity-passenger_count)
    
    # def select_passengers_with_dir_by_earliest_arrival(self, lift_dir, capacity, passenger_count):
    #     num_to_board = capacity - passenger_count
    #     passenger_df = self.passengers.df
    #     print('DEBUG onboard selection', passenger_df.loc[passenger_df.dir == lift_dir, :] \
    #         .sort_values('trip_start_time'))
    #     return passenger_df.loc[passenger_df.dir == lift_dir, :] \
    #         .sort_values('trip_start_time').head(num_to_board)
    
    def pprint_floor_passengers(self, ordering='start_time'):
        def passenger_time_format(t):
            return t.strftime("%H:%M:%S") if t is not NaT else "NA"

        def format_start_time(df):
            return df.trip_start_time.apply(passenger_time_format)
        
        def format_trip(df):
            return df.source + " -> " + df.target
        
        df = self.passengers.df.copy()
        
        df['trip'] = format_trip(df)
        df['start_time'] = format_start_time(df)

        print_cols = ['trip', 'dir', 'start_time']
        print('Floor', self.name, 'passengers waiting at', passenger_time_format(datetime.now()))
        if self.passengers.count_passengers() > 0:
            print(df.loc[:, print_cols].sort_values(ordering))
        else:
            print('floor empty')

