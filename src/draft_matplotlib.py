import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

lifts_df = pd.read_csv('../data/lift_summary.csv')
lifts_df['height'] = (lifts_df.source - lifts_df.target).abs()
lifts_df['bottom'] = lifts_df[["source", "target"]].min(axis=1)
num_lifts = lifts_df.shape[0]
lifts_df['arrowsize'] = [100 for x in range(num_lifts)]

floors_df = pd.read_csv('../data/floor_summary.csv')
floors_u_df = floors_df.loc[:,['height', 'upward_waiting']] \
    .rename(columns={'upward_waiting': 'count'})
floors_d_df = floors_df.loc[:,['height', 'downward_waiting']] \
    .rename(columns={'downward_waiting': 'count'})

density_df = pd.read_csv('../data/density_summary.csv', header=[0,1])
density_df['floor'] = density_df.iloc[:,0]
density_df['height'] = density_df.iloc[:,1]
density_df = density_df.iloc[1:,2:]
x = density_df.height 
yuw = np.array(density_df.density_up.Waiting)
yu1 = np.array(density_df.density_up['Lift A'])
yu2 = np.array(density_df.density_up['Lift B'])
yu3 = np.array(density_df.density_up['Lift C'])
yu4 = np.array(density_df.density_up['Lift D'])
yu5 = np.array(density_df.density_up['Lift E'])
ydw = np.array(density_df.density_down.Waiting)
yd1 = np.array(density_df.density_down['Lift A'])
yd2 = np.array(density_df.density_down['Lift B'])
yd3 = np.array(density_df.density_down['Lift C'])
yd4 = np.array(density_df.density_down['Lift D'])
yd5 = np.array(density_df.density_down['Lift E'])

fig = plt.figure(constrained_layout=True, figsize=(8, 9))
subfigs = fig.subfigures(2, 1)
subfig_top, subfig_bot = list(subfigs.flat)
subfig_bot.suptitle('Passenger Request Density')
ax1, ax2, ax3 = subfig_top.subplots(1, 3, sharey=True, gridspec_kw={'width_ratios': [1, 3, 1]})
axu, axd = subfig_bot.subplots(1, 2, sharey=True)

# fig, (ax1, ax2, ax3) = plt.subplots(1, 3, sharey=True, gridspec_kw={'width_ratios': [1, 3, 1]})

ax2.bar(data=lifts_df, x="lift", height="height", bottom="bottom", width=0.05, color="deepskyblue")
ax2.scatter(data=lifts_df.loc[lifts_df.dir == "U", :], x="lift", y="target", marker=6, s="arrowsize", color='gold')
ax2.scatter(data=lifts_df.loc[lifts_df.dir == "D", :], x="lift", y="target", marker=7, s="arrowsize", color='gold')
ax2.scatter(data=lifts_df.loc[lifts_df.dir == "S", :], x="lift", y="target", marker="o", s="arrowsize", color='gold')
ax2.set_yticks(ticks=[0, 17, 32, 47, 59], labels=["G", "L05", "L10", "L15", "L19"])
ax2.tick_params(left=True, right=True, labelleft=True, labelright=True)
ax2.title.set_text('Lift Locations')

ax1.barh(data=floors_u_df, y="height", width="count")
ax1.invert_xaxis()
ax1.tick_params(bottom=False, left=False, labelleft=False)
ax1.set_xlabel('Floor count')
ax1.set_frame_on(False)
ax1.title.set_text('Upward')

ax3.barh(data=floors_d_df, y="height", width="count")
ax3.tick_params(bottom=False, left=False, labelleft=False)
ax3.set_xlabel('Floor count')
ax3.set_frame_on(False)
ax3.title.set_text('Downward')

subfig_top.subplots_adjust(wspace=0.25)

# create stacked density chart
# fig, (axd, axu) = plt.subplots(1, 2, sharey=True)

axu.fill_betweenx(x, 0, yuw, label='Waiting', color='darkgray')
axu.fill_betweenx(x, yuw, yuw + yu1, label='Lift A', color='steelblue')
axu.fill_betweenx(x, yuw + yu1, yuw + yu1 + yu2, label='Lift B', color='mediumvioletred')
axu.fill_betweenx(x, yuw + yu1 + yu2, yuw + yu1 + yu2 + yu3, label='Lift C', color='mediumseagreen')
axu.fill_betweenx(x, yuw + yu1 + yu2 + yu3, yuw + yu1 + yu2 + yu3 + yu4, label='Lift D', color='mediumorchid')
axu.fill_betweenx(x, yuw + yu1 + yu2 + yu3 + yu4, yuw + yu1 + yu2 + yu3 + yu4 + yu5, label='Lift E', color='darkkhaki')
axd.fill_betweenx(x, 0, ydw, label='Waiting', color='darkgray')
axd.fill_betweenx(x, ydw, ydw + yd1, label='Lift A', color='steelblue')
axd.fill_betweenx(x, ydw + yd1, ydw + yd1 + yd2, label='Lift B', color='mediumvioletred')
axd.fill_betweenx(x, ydw + yd1 + yd2, ydw + yd1 + yd2 + yd3, label='Lift C', color='mediumseagreen')
axd.fill_betweenx(x, ydw + yd1 + yd2 + yd3, ydw + yd1 + yd2 + yd3 + yd4, label='Lift D', color='mediumorchid')
axd.fill_betweenx(x, ydw + yd1 + yd2 + yd3 + yd4, ydw + yd1 + yd2 + yd3 + yd4 + yd5, label='Lift E', color='darkkhaki')

max_x = max(axu.get_xlim()[1], axd.get_xlim()[1])
axu.set_xlim((max_x, 0))
axd.set_xlim((0, max_x))
# axd_tick_labels = axd.get_xticks()
# axd.set_xticklabels(axd_tick_labels.astype(int))
axu.tick_params(bottom=True, left=False, labelleft=True)
axd.tick_params(bottom=True, left=False, labelright=True)
axd.set_yticks([0, 5, 10, 15, 19], ['G', 'L05', 'L10', 'L15', 'L19'])
axu.legend(bbox_to_anchor=(1.2,1), loc='upper center')

plt.show()


# plt.barh(data=floor_height_df, y="Height", width="density_up", height=3, alpha=0.3)
# plt.barh(data=floor_height_df, y="Height", width="density_down", height=3, alpha=0.3)
# plt.show()

# TODO:
# make and use svg file for lift location

# show lift passenger travel density (done, to embed into a chart)
# show breakdown of overall travel density by individual lifts and waiting passengers (done)

# embed to streamlit
# perform live update on streamlit

# # customize marker from svg file
# from svgpathtools import svg2paths
# from svgpath2mpl import parse_path

# def generate_marker_from_svg(svg_path):
#     image_path, attributes = svg2paths(svg_path)

#     image_marker = parse_path(attributes[0]['d'])

#     image_marker.vertices -= image_marker.vertices.mean(axis=0)

#     image_marker = image_marker.transformed(mpl.transforms.Affine2D().rotate_deg(180))
#     image_marker = image_marker.transformed(mpl.transforms.Affine2D().scale(-1,1))

#     return image_marker