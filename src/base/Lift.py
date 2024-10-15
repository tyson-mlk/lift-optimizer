from LiftFloor import LiftFloor, MAX_FLOOR, MIN_FLOOR, FLOORS, FLOOR_HEIGHTS
from Floor import Floor
from numpy.random import choice
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
        self.passenger_targets_counter = {
            target_floor:0 
            for target_floor in FLOORS
        }
        self.calculate_passenger_count()

    def calculate_passenger_count(self) -> None:
        self.passenger_count = sum([c for ptc, c in self.passenger_targets_counter.items()])

    def get_current_floor_pc(self):
        return filter(lambda x: x.floor() == self.floor, FLOOR_PASSENGER_COUNTER)

    # untested
    def has_capacity(self):
        floor_count = self.get_current_floor_pc().get_floor_count()
        return self.passenger_count + floor_count >= LIFT_CAPACITY

    # untested
    def onboard_all(self):
        floor = self.get_current_floor_pc()
        floor.onboard_all()
        for target_floor in floor.passenger_targets():
            self.passenger_targets_counter[target_floor] += 1
        self.calculate_passenger_count()
        
    # untested
    def onboard_selected(self, floor: Floor):
        if self.has_capacity():
            selection = floor.passenger_targets()
        else:
            selection = floor.random_select_passengers()
        floor.onboard_selected(selection)
        for t in selection:
            self.passenger_targets_counter[t] += 1
        self.calculate_passenger_count()

    def alight(self):
        self.passenger_targets_counter[self.floor] = 0
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
    
    def next_passenger_target(self):
        passenger_targets = {
            t for t in self.passenger_targets_counter
            if self.passenger_targets_counter[t] > 0
        }
        if self.dir == 'U':
            floor_scan = {f for f in passenger_targets if f > self.floor}
            if len(floor_scan) > 0:
                return min(floor_scan)
            else:
                floor_scan = {f for f in passenger_targets if f < self.floor}
                if len(floor_scan) > 0:
                    return max(floor_scan)
                else:
                    return None
        else:
            floor_scan = {f for f in passenger_targets if f < self.floor}
            if len(floor_scan) > 0:
                return max(floor_scan)
            else:
                floor_scan = {f for f in passenger_targets if f > self.floor}
                if len(floor_scan) > 0:
                    return min(floor_scan)
                else:
                    return None
    
    def next_target_baseline(self, floor_counter):
        targets = {
            f for f in FLOORS
            if self.passenger_targets_counter[f] > 0 or
            floor_counter[f] > 0
        }
        if self.dir == 'U':
            floor_scan = {f for f in targets if f > self.floor}
            if len(floor_scan) > 0:
                return min(floor_scan)
            else:
                floor_scan = {f for f in targets if f < self.floor}
                if len(floor_scan) > 0:
                    return max(floor_scan)
                else:
                    return None
        else:
            floor_scan = {f for f in targets if f < self.floor}
            if len(floor_scan) > 0:
                return max(floor_scan)
            else:
                floor_scan = {f for f in targets if f > self.floor}
                if len(floor_scan) > 0:
                    return min(floor_scan)
                else:
                    return None


    # TODO: move function to main control    
    # def stop(self, floor):
    #     self.alight(floor)
    #     eligible_floors = master.get_eligible_floors(floor)
    #     master.get_floor_passengers(floor).board(eligible_floors, self)
