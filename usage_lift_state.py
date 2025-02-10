# usage example 2
# start from src/ folder
import src.base
from src.metrics.LiftSpec import LiftSpec
from src.metrics.CalcMovingFloor import CalcMovingFloor
from src.metrics.CalcAccelModelMovingStatus import  CalcAccelModelMovingStatus

m = LiftSpec()

mh = CalcMovingFloor('G', 'L05', m)
print(mh.calc_state(4))
print(mh.calc_state(8))
print(mh.calc_state(9))

mh2 = CalcMovingFloor('G', 'L02', m)
print(mh2.calc_state(2))
print(mh2.calc_state(4))
print(mh2.calc_state(6))

ms = CalcAccelModelMovingStatus(
    0, '32', 0, m
)
ms.print_status()
ms2 = CalcAccelModelMovingStatus(
    *mh.calc_state(3), m
)
ms2.print_status()
print(ms2.calc_time(3))
print(ms2.calc_time(10))
print(ms2.calc_time(16))
print(ms2.calc_time(20))
