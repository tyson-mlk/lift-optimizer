from base.Passenger import Passenger

class ArrivedPassengers(Passenger):
    def __init__(self, source, target, arrival_time):
        super().__init__(source, target)
        self.arrival_time = arrival_time
