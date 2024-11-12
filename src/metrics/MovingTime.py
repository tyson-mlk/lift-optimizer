from math import sqrt
from base.FloorList import FLOOR_LIST


class MovingTime:
    
    def __init__(self, a: float = 1.0, max_v: float = 4.0,
                 overhead: float = 2.0, model: str = "accel") -> None:
        self.a = a
        self.max_v = max_v
        self.overhead = overhead
        if model == "accel":
            self.calc_model = \
            lambda dist: MovingTime.accel_model_time(
                self.a, self.max_v, dist
            )
        elif model == "unif":
            self.calc_model = \
            lambda dist: MovingTime.uniform_model_time(
                self.overhead, self.max_v, dist
            )

    @classmethod
    def accel_model_time(cls, a, max_v, dist: float) -> float:
        accel_dist = max_v ** 2 / a
        if dist < accel_dist:
            return 2 * sqrt(dist/a)
        else:
            accel_time = 2 * max_v / a
            max_speed_dist = dist - accel_dist
            return accel_time + max_speed_dist / max_v

    @classmethod
    def uniform_model_time(cls, overhead, max_v, dist: float) -> float:
        move_time = dist / max_v
        return overhead + move_time


class MovingHeight:
    def __init__(self, source, target,
                 a: float = 1.0, max_v: float = 4.0,
                 overhead: float = 2.0, model: str = "accel") -> None:
        self.a = a
        self.max_v = max_v
        self.overhead = overhead
        self.source_height = FLOOR_LIST.get_floor(source).height
        self.target_height = FLOOR_LIST.get_floor(target).height
        # either 'U' or 'D' for moving
        self.dir = 'U' if self.target_height > self.source_height else 'D'
        self.dist = abs(self.source_height - self.target_height)
        if model == 'accel':
            self.time_to_max = self.max_v / self.a
            self.time_at_max = max( (self.dist - self.max_v ** 2 / self.a) / self.max_v, 0)
            self.calc_height = lambda t: self.accel_model_height(t)
        elif model == 'unif':
            self.calc_height = lambda t: self.uniform_model_height(t)

    def accel_model_height(self, time_elapsed):
        if time_elapsed <= 0:
            return self.source_height
        
        accel_dist = self.max_v ** 2 / self.a
        if self.dist >= accel_dist:
            if time_elapsed - self.time_to_max < 0:
                dist_traveled = self.a * time_elapsed**2 / 2
            elif time_elapsed - self.time_to_max - self.time_at_max < 0:
                accel_dist = self.max_v ** 2 / self.a / 2
                max_dist = self.max_v * (time_elapsed - self.time_to_max)
                dist_traveled = accel_dist + max_dist
            elif time_elapsed - self.time_to_max - self.time_at_max - self.time_to_max < 0:
                accel_dist = self.max_v ** 2 / self.a / 2
                max_dist = self.max_v * self.time_at_max
                decel_time = time_elapsed - self.time_to_max - self.time_at_max
                decel_dist = decel_time * (self.max_v - decel_time * self.a / 2)
                dist_traveled = accel_dist + max_dist + decel_dist
            else:
                return self.target_height
        else:
            time_to_half = sqrt(self.dist/self.a)
            if time_elapsed <= time_to_half:
                dist_traveled = time_elapsed**2 * self.a / 2
            else:
                time_est_remaining = 2 * time_to_half - time_elapsed
                if time_est_remaining < 0:
                    time_est_remaining = 0
                dist_traveled = self.dist - time_est_remaining**2 * self.a / 2
    
        if self.dir == 'U':
            return self.source_height + dist_traveled
        else:
            return self.source_height - dist_traveled

    def uniform_model_height(self, time_elapsed):
        if time_elapsed < self.overhead / 2:
            return self.source_height
        dist_traveled = (time_elapsed - self.overhead / 2) * self.max_v
        if dist_traveled > self.dist:
            return self.target_height
        else:
            if self.dir == 'U':
                return self.source_height + dist_traveled
            else:
                return self.source_height - dist_traveled
