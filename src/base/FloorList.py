from base.Floor import Floor

class FloorList:
    def __init__(self, floors, floor_heights):
        self.dict = {}

        for floorname in floors:
            self.add_floor(Floor(floorname, floor_heights[floorname]))

    def add_floor(self, floor: Floor):
        assert floor.name not in self.dict
        self.dict[floor.name] = floor
        floor.init_logger()

    def get_floor(self, floorname):
        if floorname not in self.dict:
            raise ValueError('Invalid floor name')
        return self.dict[floorname]
    
    def list_floors(self):
        return list(self.dict.keys())

FLOORS = list(str(i).zfill(3) for i in range(20))
FLOOR_HEIGHTS = {i:float(2+int(i)*3) if i != '000' else 0.0 for i in FLOORS}
FLOOR_LIST = FloorList(FLOORS, FLOOR_HEIGHTS)
MIN_FLOOR = min(FLOORS)
MAX_FLOOR = max(FLOORS)
