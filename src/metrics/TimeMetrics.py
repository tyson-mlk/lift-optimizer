from datetime import timedelta

from base.PassengerList import PassengerList


def calculate_travel_time(passengers):
    df = passengers.df
    arrived_idx = (df.dest_arrival_time.notna()) & (df.trip_start_time.notna())
    df.loc[arrived_idx, 'travel_time'] = (df.loc[arrived_idx, 'dest_arrival_time'] - df.loc[arrived_idx, 'trip_start_time'])\
        .apply(timedelta.total_seconds)
    return PassengerList(df)

def calculate_waiting_time(passengers):
    df = passengers.df
    arrived_idx = (df.board_time.notna()) & (df.trip_start_time.notna())
    df.loc[arrived_idx, 'waiting_time'] = (df.loc[arrived_idx, 'board_time'] - df.loc[arrived_idx, 'trip_start_time'])\
        .apply(timedelta.total_seconds)
    return PassengerList(df)

def calculate_time_on_lift(passengers):
    df = passengers.df
    arrived_idx = (df.dest_arrival_time.notna()) & (df.board_time.notna())
    df.loc[arrived_idx, 'time_on_lift'] = (df.loc[arrived_idx, 'dest_arrival_time'] - df.loc[arrived_idx, 'board_time'])\
        .apply(timedelta.total_seconds)
    return PassengerList(df)

def calculate_all_metrics(passengers):
    df = passengers.df
    boarded_idx = (df.board_time.notna()) & (df.trip_start_time.notna())
    arrived_idx = (df.dest_arrival_time.notna()) & (df.board_time.notna()) & (df.trip_start_time.notna())

    df.loc[boarded_idx, 'waiting_time'] = (df.loc[boarded_idx, 'board_time'] - df.loc[boarded_idx, 'trip_start_time'])\
        .dt.total_seconds()
    df.loc[arrived_idx, 'travel_time'] = (df.loc[arrived_idx, 'dest_arrival_time'] - df.loc[arrived_idx, 'trip_start_time'])\
        .dt.total_seconds()
    df.loc[arrived_idx, 'time_on_lift'] = (df.loc[arrived_idx, 'dest_arrival_time'] - df.loc[arrived_idx, 'board_time'])\
        .dt.total_seconds()
    return PassengerList(df)
