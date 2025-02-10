from math import sqrt
from src.metrics.LiftSpec import LiftSpec


class CalcAccelModelMovingStatus:
    def __init__(self, height, direction, velocity, lift_spec: LiftSpec) -> None:
        self.spec = lift_spec
        self.height = height
        self.direction = direction
        self.velocity = velocity

    def __str__(self):
        print_str = self.spec.__str__()
        return f"{print_str}, height: {self.height}, direction: {self.direction}, velocity: {self.velocity}"

    @classmethod
    def get_dist_to_stop(cls, spec, velocity):
        return velocity ** 2 / spec.a / 2

    @classmethod
    def get_time_to_stop(cls, spec, velocity):
        assert velocity >= 0
        return velocity / spec.a

    def get_status_to_stop(self):
        assert self.spec.model_type == "accel"
        assert self.direction in ['U', 'D']
        if self.direction == 'U':
            height = self.height + CalcAccelModelMovingStatus.get_dist_to_stop(self.spec, self.velocity)
        else:
            height = self.height - CalcAccelModelMovingStatus.get_dist_to_stop(self.spec, self.velocity)
        return height, self.direction, 0.0

    def get_stoppability(self, new_height):
        assert self.spec.model_type == "accel"
        assert self.direction in ['U', 'D']
        stopping_height = self.get_status_to_stop()[0]
        if self.direction == 'U':
            return stopping_height <= new_height
        else:
            return stopping_height >= new_height

    def calc_time(self, new_height):
        if self.get_stoppability(new_height) or self.direction == 'S':
            # calculate whether max speed will be reached
            time_to_max = (self.spec.max_v - self.velocity) / self.spec.a
            dist_to_max = time_to_max * (self.velocity + self.spec.max_v) / 2
            unidir_dist_to_travel = abs(new_height - self.height)
            max_reachable = unidir_dist_to_travel > (self.spec.get_accel_dist() / 2 + dist_to_max)
            if max_reachable:
                max_speed_dist = unidir_dist_to_travel - self.spec.get_accel_dist() / 2 - dist_to_max
                max_speed_time = max_speed_dist / self.spec.max_v
                return time_to_max + max_speed_time + \
                    CalcAccelModelMovingStatus.get_time_to_stop(self.spec, self.spec.max_v)
            else:
                dist_to_travel = abs(new_height - self.height)
                discriminant = self.velocity**2 / 2 + self.spec.a * dist_to_travel
                accel_time = (sqrt(discriminant) - self.velocity) / self.spec.a
                # velocity_reached = velocity + self.spec.a * accel_time
                return 2*accel_time + self.velocity / self.spec.a
        else:
            trans_time = CalcAccelModelMovingStatus.get_time_to_stop(self.spec, self.velocity)
            trans_height = self.get_status_to_stop()[0]
            distance = abs(new_height - trans_height)
            return trans_time + self.spec.calc_time(distance)
        
    # to test
    def calc_status(self, new_height, time_elapsed):
        height_mult = 1 if self.direction == 'U' else -1
        if time_elapsed > self.calc_time(new_height):
            return new_height, self.direction, 0.0
        if self.get_stoppability(new_height):
            # calculate whether max speed will be reached
            time_to_max = (self.spec.max_v - self.velocity) / self.spec.a
            dist_to_max = time_to_max * (self.velocity + self.spec.max_v) / 2
            unidir_dist_to_travel = abs(new_height - self.height)
            max_reachable = unidir_dist_to_travel > (self.spec.get_accel_dist() / 2 + dist_to_max)
            if max_reachable:
                if time_elapsed <= time_to_max:
                    v = self.velocity + self.spec.a * time_elapsed
                    dist = time_elapsed * (v + self.velocity) / 2
                    h = self.height + dist * height_mult
                    return h, self.direction, v
                max_speed_dist = unidir_dist_to_travel - self.spec.get_accel_dist() / 2 - dist_to_max
                max_speed_time = max_speed_dist / self.spec.max_v
                if time_elapsed <= time_to_max + max_speed_time:
                    v = self.spec.max_v
                    time_at_max = time_elapsed - time_to_max
                    dist = dist_to_max + time_at_max * self.spec.max_v
                    h = self.height + dist * height_mult
                    return h, self.direction, v
                time_decel = time_elapsed - time_to_max - max_speed_time
                v = self.spec.max_v - self.spec.a * time_decel
                dist = dist_to_max + max_speed_dist + time_decel * (self.spec.max_v - self.spec.a * time_decel / 2)
                h = self.height + dist * height_mult
                return h, self.direction, v
            else:
                dist_to_travel = abs(new_height - self.height)
                discriminant = self.velocity**2 / 2 + self.spec.a * dist_to_travel
                accel_time = (sqrt(discriminant) - self.velocity) / self.spec.a
                velocity_to_reach = self.velocity + self.spec.a * accel_time
                if time_elapsed <= accel_time:
                    v = self.velocity + time_elapsed * self.spec.a
                    dist = time_elapsed * (v + self.velocity) / 2
                    h = self.height + dist * height_mult
                    return h, self.direction, v
                else:
                    time_decel = time_elapsed - accel_time
                    v = velocity_to_reach - time_decel * self.spec.a
                    accel_dist = accel_time * (self.velocity + velocity_to_reach) / 2
                    dist = accel_dist + time_decel * (velocity_to_reach + v) / 2
                    h = self.height + dist * height_mult
                    return h, self.direction, v
        else:
            # TODO: find out if refactoring CalcMovingFloor.py gives more maintinable code
            trans_time = CalcAccelModelMovingStatus.get_time_to_stop(self.spec, self.velocity)
            if time_elapsed < trans_time:
                v = self.velocity - self.spec.a * time_elapsed
                dist = time_elapsed * (v + self.velocity) / 2
                h = self.height + dist * height_mult
                return h, self.direction, v
            direction = 'D' if self.direction == 'U' else 'U'
            height_mult *= -1
            trans_height = self.get_status_to_stop()[0]
            distance_to_cont = abs(new_height - trans_height)
            max_reachable = distance_to_cont > self.spec.get_accel_dist() * 2
            if max_reachable:
                if time_elapsed - trans_time <= self.spec.get_time_to_max():
                    v = (time_elapsed - trans_time) * self.spec.a
                    dist = self.spec.a * (time_elapsed - trans_time) ** 2 / 2
                    h = trans_height + dist * height_mult
                    return h, direction, v
                if time_elapsed - trans_time <= self.spec.calc_time(distance_to_cont) - self.spec.get_time_to_max():
                    time_at_max = (time_elapsed - trans_time) - LiftSpec.get_time_to_max()
                    dist = LiftSpec.get_accel_dist() + time_at_max * self.spec.max_v
                    h = trans_height + dist * height_mult
                    return h, direction, self.spec.max_v
                else:
                    time_remain =  self.spec.calc_time(distance_to_cont) - (time_elapsed - trans_time)
                    v = time_remain * self.spec.a
                    dist = distance_to_cont - self.spec.a * time_remain ** 2 / 2
                    h = trans_height + dist * height_mult
                    return h, direction, v
            else:
                if time_elapsed - trans_time <= self.spec.calc_time(distance_to_cont) / 2:
                    v = (time_elapsed - trans_time) * self.spec.a
                    dist = self.spec.a * (time_elapsed - trans_time) ** 2 / 2
                    h = trans_height + dist * height_mult
                    return h, direction, v
                else:
                    time_remain = self.spec.calc_time(distance_to_cont) - (time_elapsed - trans_time)
                    v = time_remain * self.spec.a
                    dist = distance_to_cont - self.spec.a * time_remain ** 2 / 2
                    h = trans_height + dist * height_mult
                    return h, direction, v
    

    def print_status(self):
        height_str = f'Lift at {round(self.height, 2)}m '
        if self.velocity > 0:
            velocity_str = f'moving {self.direction} with {round(self.velocity, 2)}ms-1'
        else:
            velocity_str = 'stopping'
        print_str = height_str + velocity_str
        print(print_str)
        return print_str
