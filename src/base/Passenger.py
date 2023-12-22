class Passenger:
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.floor = source
        self.lift = None

    @property
    def floor(self):
        return self._floor
    
    @property
    def lift(self):
        return self._lift
    
    @floor.setter
    def floor(self, new_floor):
        self._floor = new_floor

    @lift.setter
    def lift(self, new_lift):
        if new_lift.has_capacity():
            self._lift = new_lift
