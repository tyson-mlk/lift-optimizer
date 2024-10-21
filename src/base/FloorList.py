from base.Floor import Floor

class FloorList:
    def __init__(self, floor_data = None):
        self.dict = {}

    def add_floor(self, floor: Floor):
        assert floor.floor not in self.dict
        self.dict[floor.floor] = floor

    def get_floor(self, floor_name):
        if floor_name not in self.dict:
            raise ValueError('Invalid floor name')
        return self.dict[floor_name]
    
    def list_floors(self):
        return list(self.dict.keys())

FLOOR_LIST = FloorList()
FLOORS = list(str(i).zfill(3) for i in range(20))
FLOOR_HEIGHTS = {i:float(i) for i in FLOORS}
MIN_FLOOR = min(FLOORS)
MAX_FLOOR = max(FLOORS)
for floor in FLOORS:
    FLOOR_LIST.add_floor(Floor(floor, FLOOR_HEIGHTS[floor]))
