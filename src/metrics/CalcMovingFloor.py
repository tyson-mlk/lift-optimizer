from math import sqrt
from src.base.FloorList import FLOOR_LIST
from src.metrics.LiftSpec import LiftSpec


class CalcMovingFloor:
    def __init__(self, source, target, lift_spec: LiftSpec) -> None:
        self.spec = lift_spec
        self.source_height = FLOOR_LIST.get_floor(source).height
        self.target_height = FLOOR_LIST.get_floor(target).height
        # either 'U' or 'D' for moving
        self.dir = 'U' if self.target_height > self.source_height else 'D'
        self.dist = abs(self.source_height - self.target_height)
        if lift_spec.model_type == 'accel':
            self.time_at_max = max( (self.dist - self.spec.max_v ** 2 / self.spec.a) / self.spec.max_v, 0)
            self.calc_state = lambda t: self.accel_model_status_at(t)
        elif lift_spec.model_type == 'unif':
            self.calc_state = lambda t: self.uniform_model_status_at(t)

    def __str__(self):
        return f"{self.spec.__str__()}, source: {self.source_height}, target: {self.target_height}"

    def accel_model_reaches_max(self):
        return self.dist >= self.spec.get_accel_dist()
    
    def accel_model_distance_velocity_with_max(self, time_elapsed):
        if time_elapsed <= 0:
            return 0.0, self.dir, 0.0
        elif time_elapsed - self.spec.get_time_to_max() < 0:
            dist_traveled = self.spec.a * time_elapsed**2 / 2
            velocity = self.spec.a * time_elapsed
            return dist_traveled, self.dir, velocity
        elif time_elapsed - self.spec.get_time_to_max() - self.time_at_max < 0:
            max_dist = self.spec.max_v * (time_elapsed - self.spec.get_time_to_max())
            dist_traveled = self.spec.get_accel_dist() / 2 + max_dist
            return dist_traveled, self.dir, self.spec.max_v
        elif time_elapsed - self.spec.get_time_to_max() - self.time_at_max - self.spec.get_time_to_max() < 0:
            max_dist = self.spec.max_v * self.time_at_max
            decel_time = time_elapsed - self.spec.get_time_to_max() - self.time_at_max
            decel_dist = decel_time * (self.spec.max_v - decel_time * self.spec.a / 2)
            velocity = self.spec.max_v - decel_time * self.spec.a
            dist_traveled = self.spec.get_accel_dist() / 2 + max_dist + decel_dist
            return dist_traveled, self.dir, velocity
        else:
            return self.dist, self.dir, 0.0
        
    def accel_model_distance_velocity_no_max(self, time_elapsed):
        time_to_half = sqrt(self.dist/self.spec.a)
        if time_elapsed <= 0:
            return 0.0, self.dir, 0.0
        elif time_elapsed <= time_to_half:
            dist_traveled = time_elapsed**2 * self.spec.a / 2
            velocity = time_elapsed * self.spec.a
            return dist_traveled, self.dir, velocity
        else:
            time_est_remaining = 2 * time_to_half - time_elapsed
            if time_est_remaining < 0:
                return self.dist, self.dir, 0.0
            dist_traveled = self.dist - time_est_remaining**2 * self.spec.a / 2
            velocity = time_est_remaining * self.spec.a
            return dist_traveled, self.dir, velocity

    def accel_model_status_at(self, time_elapsed):
        if self.accel_model_reaches_max():
            dist, d, v = self.accel_model_distance_velocity_with_max(time_elapsed)
            return self.get_height(dist), d, v
        else:
            dist, d, v = self.accel_model_distance_velocity_no_max(time_elapsed)
            return self.get_height(dist), d, v

    def uniform_model_status_at(self, time_elapsed):
        if time_elapsed < self.spec.overhead / 2:
            dist_traveled = 0
            velocity = 0
        else:
            dist_traveled = (time_elapsed - self.spec.overhead / 2) * self.spec.max_v
            velocity = self.spec.max_v
            if dist_traveled > self.dist:
                dist_traveled = self.dist
                velocity = 0
    
        return self.get_height(dist_traveled), self.dir, velocity

    def get_height(self, dist_traveled):
        if self.dir == 'U':
            return self.source_height + dist_traveled
        else:
            return self.source_height - dist_traveled
