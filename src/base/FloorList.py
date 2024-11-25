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
    
    def floor_height_lookup(self):
        return {fn: f.height for fn, f in self.dict.items()}
    
    def get_max_height(self):
        return max([h for f, h in self.floor_height_lookup().items()])
    
    def get_min_height(self):
        return min([h for f, h in self.floor_height_lookup().items()])
    
    def floor_height_order(self, floor, dir):
        if dir == 'U':
            return self.get_floor(floor).height
        elif dir == 'D':
            height_extent = self.get_max_height() - self.get_min_height()
            return 2 * height_extent - self.get_floor(floor).height

FLOORS = list(str(i).zfill(3) for i in range(20))
FLOOR_HEIGHTS = {i:float(2+int(i)*3) if i != '000' else 0.0 for i in FLOORS}
FLOOR_LIST = FloorList(FLOORS, FLOOR_HEIGHTS)
MIN_FLOOR = min(FLOORS)
MAX_FLOOR = max(FLOORS)
