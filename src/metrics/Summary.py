import pandas as pd

from base.PassengerList import PASSENGERS

def lift_summary():
    return pd.DataFrame(
        [[
            lift.name, lift.floor, lift.height, lift.next_height, lift.dir
            ] for lift in PASSENGERS.tracking_lifts
        ],
        columns=['lift', 'floor', 'source', 'target', 'dir']
    )

def calc_density(df, floorname, direction):
    if direction == 'U':
        return ((df.target > floorname) & (df.current <= floorname)).sum()
    if direction == 'D':
        return ((df.target < floorname) & (df.current >= floorname)).sum()


def calc_density_by_group(df, floorname, direction, group):
    if direction == 'U':
        return ((df.target > floorname) & (df.current <= floorname) & (df.group == group)).sum()
    if direction == 'D':
        return ((df.target < floorname) & (df.current >= floorname) & (df.group == group)).sum()


def calc_density_hist(df, floorname, floorheight, direction):
    if direction == 'U':
        return [floorheight] * ((df.target > floorname) & (df.current <= floorname)).sum()
    if direction == 'D':
        return [floorheight] * ((df.target < floorname) & (df.current >= floorname)).sum()


def floor_request_snapshot(floor_list):
    return pd.DataFrame(
        [
            [
                floorname,
                floor.height,
                floor.get_floor_count(),
                floor.get_floor_passenger_count_with_dir('U'),
                floor.get_floor_passenger_count_with_dir('D')
            ] for floorname, floor in floor_list.floors
        ],
        columns = ['floor', 'height', 'total_waiting', 'upward_waiting', 'downward_waiting']
    )

def density_summary(floor_summary_df, passenger_df):
    df = floor_summary_df.loc[:, ['floor', 'height']]
    # df.columns = pd.MultiIndex.from_product([['floor'], ['floor', 'height', 'total_waiting', 'upward_waiting', 'downward_waiting']])
    passenger_df['group'] = PASSENGERS.boarded_lift_info()
    passenger_group_df = pd.Series([l.name for l in PASSENGERS.tracking_lifts] + ['Waiting'], name='lift')
    df = df.merge(passenger_group_df, how='cross')
    df['density_up'] = df \
        .apply(lambda x: calc_density_by_group(passenger_df, x.floor, 'U', x.lift), axis=1)
    df['density_down'] = df \
        .apply(lambda x: calc_density_by_group(passenger_df, x.floor, 'D', x.lift), axis=1)
    return pd.pivot_table(df, values=['density_up', 'density_down'], index=['floor', 'height'], columns=['lift'])
