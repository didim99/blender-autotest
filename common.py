import time
import statistics
from typing import List


global_log: str = None


class LogLevel:
    E = "ERR"
    W = "WARN"
    I = "INFO"
    V = "VERB"


def log_setup(path: str) -> None:
    global global_log
    global_log = path


def log_print(level: str, msg: str) -> None:
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    log = f"{now} [{level.upper()}] {msg}"
    print(log)

    if global_log is not None:
        with open(global_log, 'a') as file:
            file.write(log + '\n')


def str2ms(ts: str) -> int:
    ts = reversed(ts.split(':'))
    res = 0

    for r, t in enumerate(ts):
        if '.' in t:
            t = t.split('.')
            t = int(t[0]) * 1000 + int(t[1]) * 10
        else:
            t = int(t) * 1000
        res += t * 60 ** r

    return res


def ms2str(ts: int, sep='.') -> str:
    res = []
    for part in [1000, 60, 60]:
        res.append(ts % part)
        ts //= part
    res = "{:02d}:{:02d}{}{:03d}".format(
        res[2], res[1], sep, res[0])
    if ts > 0:
        res = "{:02d}:{}".format(ts, res)
    return res


def time_stat(times: List[int]) -> (int, float):
    avg = int(round(statistics.fmean(times)))
    dev = statistics.stdev(times)
    return avg, dev


def freq_stat(freqs: List[float]) -> (float, float):
    avg = statistics.mean(freqs)
    dev = statistics.stdev(freqs)
    return avg, dev
