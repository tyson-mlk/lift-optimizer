from math import sqrt


class LiftSpec:
    
    def __init__(self, a: float = 1.0, max_v: float = 4.0,
                 overhead: float = 2.0, model: str = "accel") -> None:
        self.a = a
        self.max_v = max_v
        self.overhead = overhead
        self.model_type = model
        if model == "accel":
            self.calc_time = \
            lambda dist: LiftSpec.accel_model_time(
                self.a, self.max_v, dist
            )
        elif model == "unif":
            self.calc_time = \
            lambda dist: LiftSpec.uniform_model_time(
                self.overhead, self.max_v, dist
            )

    def __str__(self):
        if self.model_type == "accel":
            return f"model: {self.model_type}, a: {self.a}, max_v: {self.max_v}"
        elif self.model_type == "unif":
            return f"model: {self.model_type}, max_v: {self.max_v}, overhead: {self.overhead}"

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
    
    def get_accel_dist(self):
        return self.max_v ** 2 / self.a
    
    def get_time_to_max(self):
        return self.max_v / self.a
