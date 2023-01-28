import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
import time

path = "data/2023-01-24_19-28-32.csv"

data = pd.read_csv(path, sep=";")
version_count = data['version'].nunique()
wd = 0.18
versions = data['version'].unique()
render_label = data['renderer'].unique()
experiment_title = data['model'].unique()
# print(versions)
fig, ax = plt.subplots(2, 1)
formatter = matplotlib.ticker.FuncFormatter(lambda ms, x: time.strftime('%M:%S', time.gmtime(ms // 1000)))

for i, title in enumerate(experiment_title):
    values = {}
    max_time = data[(data["model"] == title)]["time_ms"].max()
    for v in versions:
        current_data2 = data[(data["model"] == title) & (data["version"] == v)]
        positions = [np.arange(len(current_data2)) - list(versions).index(v) * (wd) for v in versions]
        colors = [(0, i / max_time, 0) for i in current_data2["time_ms"].values]

        cur_bar = ax[i].barh(np.arange(len(current_data2)) - list(versions).index(v) * (wd) + 0.45,
                             current_data2["time_ms"], height=wd, label=v, color=colors, linewidth=0.4, edgecolor='k')
        ax[i].bar_label(cur_bar, labels=[v for v in current_data2["version"]],
                        padding=8, fontsize=12)

    ax[i].set(yticks=np.arange(len(render_label)) + wd, yticklabels=render_label, ylim=[2 * wd - 1, len(render_label)])
    # ax[i].legend()
    ax[i].xaxis.set_major_formatter(formatter)
    ax[i].set_title(title)
    ax[i].set_axisbelow(True)
    ax[i].grid(color='gray', linestyle=':')

plt.show()
