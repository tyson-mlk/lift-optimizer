from LiftFloor import LiftFloor, MAX_FLOOR, MIN_FLOOR, FLOORS, FLOOR_HEIGHTS
from Passenger import Passenger

LIFT_CAPACITY = 12
    
class Lift:
    "lift class"

    def __init__(self, lift_floor) -> None:
        assert type(lift_floor) is LiftFloor

        self.floor = lift_floor.floor
        self.dir = lift_floor.dir
        self.passengers: list[Passenger] = []
        self.passenger_targets_counter = {
            target_floor:0 
            for target_floor in FLOORS
        }

    def onboard(self, passengers: list[Passenger]):
        self.passengers.extend(passengers)
        for passenger in passengers:
            self.passenger_targets_counter[passenger.target] += 1

    def alight(self, floor):
        self.passenger_targets_counter[floor] = 0
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
