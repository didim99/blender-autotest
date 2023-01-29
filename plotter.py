import os.path
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, FuncFormatter

from blender import DeviceType


device_colors = {
    DeviceType.CPU: {'min': (15, 55, 107), 'max': (121, 173, 236)},
    DeviceType.CUDA: {'min': (13, 97, 3), 'max': (172, 246, 162)},
    DeviceType.OPTIX: {'min': (115, 2, 11), 'max': (232, 151, 158)}
}


def time_format(ms: float, _) -> str:
    if ms < 60 * 1000:
        return f'{ms // 1000:02.0f}.{ms % 1000:02.0f}'
    return time.strftime('%M:%S', time.gmtime(ms // 1000))


def mix(col0: tuple, col1: tuple, ratio: float) -> tuple:
    return tuple((cmp1 * ratio + cmp0 * (1 - ratio)) / 255
                 for cmp0, cmp1 in zip(col0, col1))


def get_color(v: float, renderer: str) -> tuple:
    color = device_colors[renderer]
    return mix(color['min'], color['max'], v)


def make_plot(file_path):
    lh = 0.1

    data = pd.read_csv(file_path, sep=";")
    versions = data['version'].unique()
    renderers = data['renderer'].unique()
    model_names = data['model'].unique()

    # For every model drew a separate plot
    for model in model_names:
        max_time = data[(data["model"] == model)]["time_ms"].max()
        fig, ax = plt.subplots()
        fig.set_dpi(150)

        y_ticks = None
        # Draw results grouped by 'renderer' column
        for i, renderer in enumerate(renderers):
            current_data = data[(data["model"] == model) & (data["renderer"] == renderer)]
            # Calculate bar colors based on renderer type and elapsed time
            colors = [get_color(i/max_time, renderer) for i in current_data["time_ms"].values]
            # Calculate global Y offset for current group
            y_offs = (len(versions) + 1) * lh * i

            # Store Y positions to draw Y-ticks later
            cur_ticks = np.arange(len(versions)) * lh + y_offs
            if y_ticks is None:
                y_ticks = np.copy(cur_ticks)
            else:
                y_ticks = np.concatenate([y_ticks, cur_ticks])

            # Calculate range of offsets for Y positions in current group
            # by intersecting all version names and version names presented
            # in group and taking indexes of 'ones' in intersection table
            cur_y = np.nonzero(np.in1d(versions, current_data['version']))[0]

            # Draw bars and labels for current group
            cur_bar = ax.barh(cur_y * lh + y_offs, current_data["time_ms"],
                              height=lh, label=renderer, color=colors,
                              linewidth=0.4, edgecolor='k')
            ax.bar_label(cur_bar, labels=[v for v in current_data["time"]],
                         padding=4, fontsize=10)

        # Configure grid
        ax.xaxis.set_major_formatter(FuncFormatter(time_format))
        ax.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax.xaxis.grid(which='both', color='gray', linestyle=':')
        ax.xaxis.grid(which='minor', alpha=0.5)

        # Configure other stuff
        ax.margins(x=0.2)
        ax.set_title(model)
        ax.set_axisbelow(True)
        ax.set(yticks=y_ticks,
               yticklabels=np.tile(versions, len(renderers)))
        ax.legend(loc='lower center', ncols=len(renderers),
                  bbox_to_anchor=(0.5, -0.18))
        plt.tight_layout()

        # Show figure
        name = os.path.splitext(file_path)[0]
        name += '_' + model + '.png'
        plt.savefig(name, dpi=300)

        # Save figure in PNG file
        win_title = os.path.basename(file_path) + ' - ' + model
        fig.canvas.manager.set_window_title(win_title)
        plt.show()


def run():
    basedir = os.getcwd()
    out_dir = os.path.join(basedir, 'out')

    for file in sorted(os.listdir(out_dir)):
        if not file.endswith('.csv'):
            continue

        path = os.path.join(out_dir, file)
        make_plot(path)


if __name__ == '__main__':
    run()
