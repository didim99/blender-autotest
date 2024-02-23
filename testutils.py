from __future__ import annotations

import copy
import os
import re
import statistics
from typing import List, Union

from blender import BlenderExe
from common import ms2str, str2ms, time_stat
from hwmeters import freqstat


class TestModel(object):
    pathCpu: str = None
    pathGpu: str = None
    name: str = None

    def __init__(self, name):
        self.name = name

    def __lt__(self, other: TestModel):
        return self.name < other.name

    def __repr__(self):
        res = f"Model '{self.name}'"
        _type = ""

        if self.pathCpu is not None:
            _type = "CPU"
        if self.pathGpu is not None:
            if len(_type) > 0:
                _type += "/"
            _type += "GPU"

        if len(_type) > 0:
            res += f" [{_type}]"
        return res


class TestConfig(object):
    blender: BlenderExe = None
    model: TestModel = None
    passes: int = None
    monitor_cpu: bool = None

    tempDir: str = None
    logPath: str = None
    outFile: str = None

    def __init__(self, blender: BlenderExe,
                 model: TestModel, passes: int = 3,
                 monitor_cpu: bool = True):
        self.passes = passes
        self.monitor_cpu = monitor_cpu
        self.blender = blender
        self.model = model

    def build(self, tmp_dir: str, log_dir: str) -> None:
        name = f"{self.model.name}_{self.blender.versionName}"
        self.logPath = os.path.join(log_dir, name)
        self.tempDir = tmp_dir
        self.outFile = os.path.join(self.tempDir, "render-")


class TestResult(object):
    passes: int = None
    blender: BlenderExe = None
    model: TestModel = None
    renderer: str = None
    times: List[int] = None
    freqs: List[freqstat] = None

    def __init__(self, config: TestConfig,
                 renderer: str, times: List[int]):
        self.model = config.model
        self.blender = config.blender
        self.passes = config.passes
        self.renderer = renderer
        self.times = times

    def add_freq_stat(self, stats: List[freqstat]):
        self.freqs = copy.copy(stats)

    @property
    def cpufreq_max(self) -> float:
        if not self.freqs:
            return 0
        return max([freq.max for freq in self.freqs])

    @property
    def cpufreq_avg(self) -> float:
        if not self.freqs:
            return 0
        return statistics.fmean([freq.avg for freq in self.freqs])

    def __str__(self):
        avg, dev = time_stat(self.times)
        return ";".join([
            self.model.name,
            self.blender.versionName,
            self.renderer,
            str(self.passes),
            str(avg),
            ms2str(avg),
            f"{dev:.03f}",
            f"{self.cpufreq_max:.03f}",
            f"{self.cpufreq_avg:.03f}",
        ])

    @staticmethod
    def header():
        return ";".join([
            'model',
            'version',
            'renderer',
            'passes',
            'time_ms',
            'time',
            'stddev_ms',
            'cpufreq_max',
            'cpufreq_avg'
        ])


def time_from_log(line: List[str]) -> int:
    return str2ms(line[1][5:])


def parse_result(result: Union[bytes, str]) -> (int, int):
    if type(result) is bytes:
        result = str(result, 'utf-8')
    lines = result.split('\n')

    bound = False
    time_str = None
    for line in reversed(lines):
        line = line.strip()
        if len(line) == 0:
            continue

        if not bound:
            if line == 'Blender quit':
                bound = True
            else:
                continue

        if line.startswith('Time:'):
            time_str = line
            break

    if not time_str:
        print(result)
        raise RuntimeError('failed to find rendering time')

    m = re.search(r"Time:\s(?P<total>[\d.:]+)\s\(Saving:\s(?P<save>[\d.:]+)\)",
                  time_str)

    total = str2ms(m.group('total'))
    save = str2ms(m.group('save'))
    render_time = total - save

    init_start = None
    init_end = None
    for line in lines:
        if not (line.startswith("Fra:") or line.startswith("Кадр:")):
            continue
        line = line.split(" | ")
        if line[-1].startswith("Loading render kernels"):
            init_start = time_from_log(line)
            continue
        if init_start is not None:
            init_end = time_from_log(line)
            break

    init_time = init_end - init_start
    return init_time, render_time
