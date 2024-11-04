from base.Floor import Floor

class FloorList:
    def __init__(self, floor_data = None):
        self.dict = {}

    def add_floor(self, floor: Floor):
        assert floor.name not in self.dict
        self.dict[floor.name] = floor

    def get_floor(self, floorname):
        if floorname not in self.dict:
            raise ValueError('Invalid floor name')
        return self.dict[floorname]
    
    def list_floors(self):
        return list(self.dict.keys())

FLOOR_LIST = FloorList()
FLOORS = list(str(i).zfill(3) for i in range(20))
FLOOR_HEIGHTS = {i:float(2+int(i)*3) if i != '000' else 0.0 for i in FLOORS}
MIN_FLOOR = min(FLOORS)
MAX_FLOOR = max(FLOORS)
for floorname in FLOORS:
    FLOOR_LIST.add_floor(Floor(floorname, FLOOR_HEIGHTS[floorname]))
