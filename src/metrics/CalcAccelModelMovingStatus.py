from math import sqrt
from metrics.LiftSpec import LiftSpec


class CalcAccelModelMovingStatus:
    def __init__(self, height, direction, velocity, lift_spec: LiftSpec) -> None:
        self.spec = lift_spec
        self.height = height
        self.direction = direction
        self.velocity = velocity

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
            return stopping_height < new_height
        else:
            return stopping_height > new_height

    def calc_time(self, new_height):
        if self.get_stoppability(new_height):
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

    def print_status(self):
        height_str = f'Lift at {round(self.height, 2)}m '
        if self.velocity > 0:
            velocity_str = f'moving {self.direction} with {round(self.velocity, 2)}ms-1'
        else:
            velocity_str = 'stopping'
        print_str = height_str + velocity_str
        print(print_str)
        return print_str
