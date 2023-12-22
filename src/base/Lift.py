from LiftFloor import LiftFloor, MAX_FLOOR, MIN_FLOOR, FLOORS, FLOOR_HEIGHTS

LIFT_CAPACITY = 12
    
class Lift:
    "lift class"

    def __init__(self, lift_floor) -> None:
        assert type(lift_floor) is LiftFloor

        self.floor = lift_floor.floor
        self.dir = lift_floor.dir
        self.passenger_count = 0
        self.passenger_targets = {
            target_floor:0 
            for target_floor in FLOORS
        }

    def onboard(self, passengers):
        for passenger in passengers:
            self.passenger_targets[passenger.target] += 1

    def alight(self, floor):
        arrived_count = self.passenger_targets[floor]
        self.passenger_count -= arrived_count
        self.passenger_targets[floor] = 0
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

    # TODO: move function to main control    
    # def stop(self, floor):
    #     self.alight(floor)
    #     eligible_floors = master.get_eligible_floors(floor)
    #     master.get_floor_passengers(floor).board(eligible_floors, self)
