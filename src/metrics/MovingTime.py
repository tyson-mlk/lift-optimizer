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
            self.accel_dist = self.max_v ** 2 / self.a
            self.time_to_max = self.max_v / self.a
            self.time_at_max = max( (self.dist - self.max_v ** 2 / self.a) / self.max_v, 0)
            self.calc_state = lambda t: self.accel_model_status(t)
        elif model == 'unif':
            self.calc_state = lambda t: self.uniform_model_status(t)

    def accel_model_reaches_max(self):
        accel_dist = self.max_v ** 2 / self.a
        return self.dist >= accel_dist
    
    def accel_model_distance_velocity_with_max(self, time_elapsed):
        if time_elapsed <= 0:
            return 0.0, self.dir, 0.0
        elif time_elapsed - self.time_to_max < 0:
            dist_traveled = self.a * time_elapsed**2 / 2
            velocity = self.a * time_elapsed
            return dist_traveled, self.dir, velocity
        elif time_elapsed - self.time_to_max - self.time_at_max < 0:
            self.accel_dist = self.max_v ** 2 / self.a / 2
            max_dist = self.max_v * (time_elapsed - self.time_to_max)
            dist_traveled = self.accel_dist + max_dist
            return dist_traveled, self.dir, self.max_v
        elif time_elapsed - self.time_to_max - self.time_at_max - self.time_to_max < 0:
            self.accel_dist = self.max_v ** 2 / self.a / 2
            max_dist = self.max_v * self.time_at_max
            decel_time = time_elapsed - self.time_to_max - self.time_at_max
            decel_dist = decel_time * (self.max_v - decel_time * self.a / 2)
            velocity = self.max_v - decel_time * self.a
            dist_traveled = self.accel_dist + max_dist + decel_dist
            return dist_traveled, self.dir, velocity
        else:
            return self.dist, self.dir, 0.0
        
    def accel_model_distance_velocity_no_max(self, time_elapsed):
        time_to_half = sqrt(self.dist/self.a)
        if time_elapsed <= 0:
            return 0.0, self.dir, 0.0
        elif time_elapsed <= time_to_half:
            dist_traveled = time_elapsed**2 * self.a / 2
            velocity = time_elapsed * self.a
            return dist_traveled, self.dir, velocity
        else:
            time_est_remaining = 2 * time_to_half - time_elapsed
            if time_est_remaining < 0:
                return self.dist, self.dir, 0.0
            dist_traveled = self.dist - time_est_remaining**2 * self.a / 2
            velocity = time_est_remaining * self.a
            return dist_traveled, self.dir, velocity

    def accel_model_status(self, time_elapsed):
        if self.accel_model_reaches_max():
            dist, d, v = self.accel_model_distance_velocity_with_max(time_elapsed)
            return self.get_height(dist), d, v
        else:
            dist, d, v = self.accel_model_distance_velocity_no_max(time_elapsed)
            return self.get_height(dist), d, v

    def uniform_model_status(self, time_elapsed):
        if time_elapsed < self.overhead / 2:
            dist_traveled = 0
            velocity = 0
        else:
            dist_traveled = (time_elapsed - self.overhead / 2) * self.max_v
            velocity = self.max_v
            if dist_traveled > self.dist:
                dist_traveled = self.dist
                velocity = 0
    
        return self.get_height(dist_traveled), self.dir, velocity

    def get_height(self, dist_traveled):
        if self.dir == 'U':
            return self.source_height + dist_traveled
        else:
            return self.source_height - dist_traveled
        
    def print_status(self, height, direction, velocity):
        height_str = f'Lift at {round(height, 2)}m '
        if velocity > 0:
            velocity_str = f'moving {direction} at {round(velocity, 2)}ms-1'
        else:
            velocity_str = 'stopping'
        print(height_str + velocity_str)
