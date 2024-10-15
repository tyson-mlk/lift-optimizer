from LiftFloor import LiftFloor, MAX_FLOOR, MIN_FLOOR, FLOORS, FLOOR_HEIGHTS
from Floor import Floor
from Passengers import Passengers
from numpy.random import choice
import pandas as pd
from collections import Counter
# from Passenger import Passenger

LIFT_CAPACITY = 12
# to initialize
global FLOOR_PASSENGER_COUNTER

class Lift:
    "lift class"

    def __init__(self, lift_floor) -> None:
        assert type(lift_floor) is LiftFloor

        self.floor = lift_floor.floor
        self.dir = lift_floor.dir
        self.passengers: Passengers = Passengers()
        self.calculate_passenger_count()

    def calculate_passenger_count(self) -> None:
        self.passenger_count = self.passengers.passenger_list.shape[0]

    def get_current_floor_count(self):
        return FLOOR_PASSENGER_COUNTER.loc[
            FLOOR_PASSENGER_COUNTER.source_floor == self.floor, :
        ]

    # untested
    def has_capacity(self):
        floor_count = self.get_current_floor_pc().get_floor_count()
        return self.passenger_count + floor_count >= LIFT_CAPACITY

    # untested
    def onboard_all(self):
        floor = self.get_current_floor_pc()
        floor.onboard_all()
        self.passengers.passenger_list = pd.concat([
            self.passengers.passenger_list,
            floor.passengers.passenger_list
        ])
        self.calculate_passenger_count()
        
    # untested
    def onboard_selected(self, floor: Floor):
        if self.has_capacity():
            selection = floor.passengers.passenger_list
        else:
            selection = floor.random_select_passengers()
        floor.onboard_selected(selection)
        self.passengers.passenger_list = pd.concat([
            self.passengers.passenger_list,
            selection
        ])
        self.calculate_passenger_count()

    def alight(self):
        self.passengers.passenger_list = self.passengers.passenger_list.loc[[],:]
        # TODO: to log arrival times of passengers

    def move(self, floor):
        if floor == MIN_FLOOR:
            self.dir = 'U'
        elif floor == MAX_FLOOR:
            self.dir = 'D'
        else:
            if floor > self.floor:
                self.dir = 'U'
            elif floor < self.floor:
                self.dir = 'D'
            else:
                self.dir = 'S'
        
        self.floor = floor

    def time_to_move(self, new_floor, old_floor, distance_lookup):
        "distance lookup function takes into account time for acceleration and deceleration"
        new_height = FLOOR_HEIGHTS[new_floor]
        old_height = FLOOR_HEIGHTS[old_floor]
        return distance_lookup( abs( new_height - old_height))
    
    def next_lift_passenger_target(self):
        passenger_targets = self.passengers.passenger_list.loc[
            :,['source_floor', 'dir']
        ].drop_duplicates()
        if passenger_targets.shape[0] == 0:
            return None
        if self.dir == 'U':
            floor_scan = passenger_targets.loc[
                (passenger_targets.source_floor > self.floor) &
                (passenger_targets.dir == 'U'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.min()
            floor_scan = passenger_targets.loc[
                (passenger_targets.dir == 'D'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.max()
            return passenger_targets.source_floor.min()
        elif self.dir == 'D':
            floor_scan = passenger_targets.loc[
                (passenger_targets.source_floor < self.floor) &
                (passenger_targets.dir == 'D'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.min()
            floor_scan = passenger_targets.loc[
                (passenger_targets.dir == 'U'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.min()
            return passenger_targets.source_floor.max()
    
    def next_overall_target_baseline(self):
        passenger_targets = pd.concat([
            FLOOR_PASSENGER_COUNTER,
            self.passengers.passenger_list
        ]).loc[:,['source_floor', 'dir']].drop_duplicates()
        if passenger_targets.shape[0] == 0:
            return None
        if self.dir == 'U':
            floor_scan = passenger_targets.loc[
                (passenger_targets.source_floor > self.floor) &
                (passenger_targets.dir == 'U'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.min()
            floor_scan = passenger_targets.loc[
                (passenger_targets.dir == 'D'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.max()
            return passenger_targets.source_floor.min()
        elif self.dir == 'D':
            floor_scan = passenger_targets.loc[
                (passenger_targets.source_floor < self.floor) &
                (passenger_targets.dir == 'D'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.min()
            floor_scan = passenger_targets.loc[
                (passenger_targets.dir == 'U'), :
            ]
            if floor_scan.shape[0] > 0:
                return floor_scan.source_floor.min()
            return passenger_targets.source_floor.max()


    # TODO: move function to main control    
    # def stop(self, floor):
    #     self.alight(floor)
    #     eligible_floors = master.get_eligible_floors(floor)
    #     master.get_floor_passengers(floor).board(eligible_floors, self)
