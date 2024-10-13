FLOORS = list(str(i).zfill(3) for i in range(20))
FLOOR_HEIGHTS = {str(i).zfill(3):i for i in range(20)}
MIN_FLOOR = FLOORS[0]
MAX_FLOOR = FLOORS[-1]
DIRS = [
    'U',
    'D',
    'W'
]

# from PreBoardPassengers import PreBoardPassengers
# from ArrivedPassengers import ArrivedPassengers

class LiftFloor:
    def __init__(self, floor, dir) -> None:
        assert floor in FLOORS
        assert dir in DIRS

        self.floor = floor
        self.dir = dir

    @property
    def floor(self):
        return self._floor
