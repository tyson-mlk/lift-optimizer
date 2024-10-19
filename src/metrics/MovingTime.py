from math import sqrt

import pandas as pd


class MovingTime:
    
    def __init__(self, a, max_v, floor_heights: dict[str, float]) -> None:
        self.floor_heights = floor_heights
        num_floors = len(floor_heights)
        self.a = a
        self.max_v = max_v
        self.time_mat = pd.DataFrame(
            [[None] * num_floors] * num_floors,
            columns = floor_heights.keys(),
            index = floor_heights.keys()
        )
        self.calc_model = None

    def accel_model_time(self, dist: float) -> float:
        accel_dist = self.max_v ** 2 / self.a
        if dist < accel_dist:
            return 2 * sqrt(dist/self.a)
        else:
            accel_time = 2 * self.max_v / self.a
            max_speed_dist = dist - accel_dist
            return accel_time + max_speed_dist / self.max_v

    def calc_accel_model(self) -> pd.DataFrame:
        self.calc_model = "accel"
        for f1 in self.floor_heights.keys():
            for f2 in self.floor_heights.keys():
                if f1 == f2:
                    continue
                self.floor_heights[f1, f2] = self.accel_model_time(
                    abs(self.floor_heights[f1] - self.floor_heights[f2])
                )
