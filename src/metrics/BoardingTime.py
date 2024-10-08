# problem with import
# import sys
# sys.path.append('..')
# from base.Lift import LIFT_CAPACITY

LIFT_CAPACITY = 10

class BoardingTime:
    def __init__(self, pre_board_cnt, boarding_off_cnt, boarding_on_cnt) -> None:
        self.pre_board_cnt = pre_board_cnt
        self.boarding_off_cnt = boarding_off_cnt
        self.boarding_on_cnt = boarding_on_cnt
        self.semi_cnt = pre_board_cnt - boarding_off_cnt
        self.after_board_cnt = pre_board_cnt - boarding_off_cnt + boarding_on_cnt
        if self.after_board_cnt > LIFT_CAPACITY:
            self.after_board_cnt = LIFT_CAPACITY

    def pre_board_saturation(self):
        return self.pre_board_cnt / LIFT_CAPACITY
    
    def post_board_saturation(self):
        desired_cnt = self.pre_board_cnt - self.boarding_off_cnt + self.boarding_on_cnt
        return min(desired_cnt / LIFT_CAPACITY, 1.0)

    def calc_boarding_time(self) -> float:
        off_board_congested = max(self.pre_board_cnt - 0.5 * LIFT_CAPACITY, 0.0)
        off_board_uncongested = max(LIFT_CAPACITY * 0.5 - self.semi_cnt, 0.0)
        on_board_uncongested = max(LIFT_CAPACITY * 0.5 - self.semi_cnt, 0.0)
        on_board_congested = max(self.after_board_cnt - 0.5 * LIFT_CAPACITY, 0.0)

        return (off_board_uncongested + on_board_uncongested) * 0.5 \
            + (off_board_congested + on_board_congested) * 1.5
