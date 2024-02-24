import platform
import statistics
import time
from collections import namedtuple
from threading import Thread
from typing import List

import distro
import psutil


freqsample = namedtuple('freqsample', ['time', 'freq'])
freqstat = namedtuple('freqstat', ['min', 'max', 'avg'])


def get_os_string() -> str:
    system = platform.system()
    if system.lower() == 'linux':
        return f"{system} {distro.name()} {distro.version()} ({platform.release()})"
    else:
        return f"{system} {platform.release()} {platform.version()}"


class CPUFreqWatcher(object):
    _running: bool = False
    _interval: float = 0.5
    _thread: Thread = None

    _buffer: List[freqsample] = None

    def __init__(self, interval: float = 0.5):
        self._interval = interval

    def run(self) -> None:
        self._buffer = []
        self._running = True
        self._thread = Thread(target=self._watch_loop, name="cpu-monitor")
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def get_stat(self):
        freq_list = [item.freq for item in self._buffer]
        return freqstat(min=min(freq_list), max=max(freq_list),
                        avg=statistics.fmean(freq_list))

    def get_csv_header(self, sep: str = ";") -> str:
        return sep.join(["time", "frequency"])

    def write_csv(self, file: str, sep: str = ";") -> None:
        with open(file, 'a') as out:
            out.write(self.get_csv_header(sep) + '\n')
            for item in self._buffer:
                out.write(sep.join([str(item.time),
                                    str(item.freq)]) + '\n')

    def _watch_loop(self) -> None:
        while self._running:
            sample = freqsample(time.time(), psutil.cpu_freq().current)
            self._buffer.append(sample)
            time.sleep(self._interval)
