from src.base.Lift import Lift


def boarding_time(lift: Lift, pre_board_cnt, boarding_off_cnt, boarding_on_cnt) -> float:
    capacity = lift.capacity
    semi_cnt = pre_board_cnt - boarding_off_cnt
    after_board_cnt = pre_board_cnt - boarding_off_cnt + boarding_on_cnt
    if after_board_cnt > capacity:
        after_board_cnt = capacity

    off_board_congested = min(max(pre_board_cnt - 0.5 * capacity, 0.0), pre_board_cnt - semi_cnt)
    off_board_uncongested = min(max(capacity * 0.5 - semi_cnt, 0.0), pre_board_cnt - semi_cnt)
    on_board_uncongested = min(max(capacity * 0.5 - semi_cnt, 0.0), after_board_cnt - semi_cnt)
    on_board_congested = min(max(after_board_cnt - 0.5 * capacity, 0.0), after_board_cnt - semi_cnt)

    return (off_board_uncongested + on_board_uncongested) * 0.5 \
        + (off_board_congested + on_board_congested) * 1.5
