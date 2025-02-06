import asyncio
import streamlit as st

from sim.PAMultLift import main

# l1 = Lift('l1', '000', 'U')

# PASSENGERS.passenger_arrival(Passenger('004', '000', datetime.now()))
# PASSENGERS.passenger_arrival(Passenger('008', '010', datetime.now()))

# async def main():
#     task = asyncio.create_task(l1.lift_baseline_operation())
#     await task

st.title('Lift Optim (dev)')

asyncio.run(main())

# from datetime import datetime
# import pandas as pd
# import asyncio

# import base
# from metrics.Summary import floor_request_snapshot, density_summary

# p_list = base.PassengerList.PASSENGERS
# p1 = base.Passenger.Passenger('001', '010', datetime.now())
# p1_df = base.PassengerList.PassengerList.passenger_to_df(p1) 
# p2 = base.Passenger.Passenger('001', '000', datetime.now())
# p2_df = base.PassengerList.PassengerList.passenger_to_df(p2)
# pp12 = base.PassengerList.PassengerList(pd.concat([p1_df, p2_df]))
# p_list.passenger_list_arrival(pp12)
# # p_list.passenger_arrival(base.Passenger.Passenger('000', '010', datetime.now()))
# # p_list.passenger_arrival(base.Passenger.Passenger('000', '002', datetime.now()))
# async def arrive_two_passengers():
#     await p_list.passenger_arrival(base.Passenger.Passenger('010', '000', datetime.now()))
#     await p_list.passenger_arrival(base.Passenger.Passenger('010', '009', datetime.now()))
# s_list = base.PassengerList.PassengerList(p_list.df.loc[p_list.df.index==2,:])

# asyncio.run(arrive_two_passengers())

# f_list = base.FloorList.FLOOR_LIST
# p_list.pprint_passenger_status(f_list)

# ground = f_list.get_floor('000')
# first = f_list.get_floor('001')
# tenth = f_list.get_floor('010')

# l1 = base.Lift.Lift('l1', '000', 'U')
# l1.capacity = 5
# l2 = base.Lift.Lift('l2', '010', 'U')

# p_list.assign_lift_for_selection(l1, s_list)
# print(p_list.df)
# print(l1.get_total_assigned())

# l1.assign_passengers(tenth.name, p_list)

# print(p_list.df)
# print(l1.passengers.df)
# print(tenth.passengers.df)
# print(l1.get_total_assigned())

# p_list.assign_lift_for_floor(l1, ground)
# p_list.assign_lift_for_selection(l2, s_list)

