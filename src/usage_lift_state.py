# usage example 2
# start from src/ folder
import base
from metrics.LiftSpec import LiftSpec
from metrics.CalcMovingFloor import CalcMovingFloor
from metrics.CalcAccelModelMovingStatus import  CalcAccelModelMovingStatus

m = LiftSpec()

mh = CalcMovingFloor('000', '005', m)
mh.calc_state(4)
mh.calc_state(8)
mh.calc_state(9)

mh2 = CalcMovingFloor('000', '002', m)
mh2.calc_state(2)
mh2.calc_state(4)
mh2.calc_state(6)

ms = CalcAccelModelMovingStatus(
    0, '32', 0, m
)
ms.print_status()
ms2 = CalcAccelModelMovingStatus(
    *mh.calc_state(3), m
)
ms2.print_status()
ms2.calc_time(3)
ms2.calc_time(10)
ms2.calc_time(16)
ms2.calc_time(20)

# from metrics.TimeMetrics import calculate_all_metrics

# calculate_all_metrics(p_list).df
