import re
import time
from typing import Union, List


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
        if not line.startswith("Fra:"):
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
