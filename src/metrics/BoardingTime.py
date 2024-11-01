from base.Lift import Lift

class BoardingTime:
    def __init__(self, lift: Lift, pre_board_cnt, boarding_off_cnt, boarding_on_cnt) -> None:
        self.capacity = lift.capacity
        self.pre_board_cnt = pre_board_cnt
        self.boarding_off_cnt = boarding_off_cnt
        self.boarding_on_cnt = boarding_on_cnt
        self.semi_cnt = pre_board_cnt - boarding_off_cnt
        self.after_board_cnt = pre_board_cnt - boarding_off_cnt + boarding_on_cnt
        if self.after_board_cnt > self.capacity:
            self.after_board_cnt = self.capacity

    def pre_board_saturation(self):
        return self.pre_board_cnt / self.capacity
    
    def post_board_saturation(self):
        desired_cnt = self.pre_board_cnt - self.boarding_off_cnt + self.boarding_on_cnt
        return min(desired_cnt / self.capacity, 1.0)

    def calc_boarding_time(self) -> float:
        off_board_congested = min(max(self.pre_board_cnt - 0.5 * self.capacity, 0.0), self.pre_board_cnt - self.semi_cnt)
        off_board_uncongested = min(max(self.capacity * 0.5 - self.semi_cnt, 0.0), self.pre_board_cnt - self.semi_cnt)
        on_board_uncongested = min(max(self.capacity * 0.5 - self.semi_cnt, 0.0), self.after_board_cnt - self.semi_cnt)
        on_board_congested = min(max(self.after_board_cnt - 0.5 * self.capacity, 0.0), self.after_board_cnt - self.semi_cnt)

        return (off_board_uncongested + on_board_uncongested) * 0.5 \
            + (off_board_congested + on_board_congested) * 1.5
