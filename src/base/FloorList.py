import pandas as pd

from src.base.Floor import Floor

class FloorList:
    def __init__(self, floors, floor_heights):
        self.floors = []
        self.floornames = []

        for floorname in floors:
            self.add_floor(Floor(floorname, floor_heights[floorname]))

    def add_floor(self, floor: Floor):
        assert floor.name not in self.floornames
        self.floornames += [floor.name]
        self.floors += [[floor.name, floor]]
        floor.init_logger()

    def get_floor(self, floorname):
        if floorname is None:
            return None
        if floorname not in self.floornames:
            raise ValueError('Invalid floor name')
        return [f[1] for f in self.floors if f[0] == floorname][0]
    
    def list_floors(self):
        return self.floornames
    
    def floor_height_lookup(self):
        return {fn: f.height for fn, f in self.floors}
    
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

    # # to init test
    # def height_queue_order(self, target_height, target_dir, height, dir):
    #     height_extent = self.get_max_height() - self.get_min_height()
    #     if target_dir == 'U':
    #         if dir == target_dir:
    #             if height < target_height:
    #                 return target_height - height
    #             else:
    #                 return 2*height_extent - (height - target_height)
    #         else:
    #             return height + target_height
    #     elif target_dir == 'D':
    #         if dir == target_dir:
    #             if height > target_height:
    #                 return height - target_height
    #             else:
    #                 return 2*height_extent - (target_height - height)
    #         else:
    #             return 2*height_extent - (height + target_height)

FLOORS = ['G'] + list('L' + str(i).zfill(2) for i in range(1, 20))
FLOOR_HEIGHTS = {i:float(2+int(i[1:])*3) if i != 'G' else 0.0 for i in FLOORS}
FLOOR_LIST = FloorList(FLOORS, FLOOR_HEIGHTS)
MIN_FLOOR = min(FLOORS)
MAX_FLOOR = max(FLOORS)
