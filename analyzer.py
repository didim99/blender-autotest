import os
import time

from blender import INIT_THRESHOLD
from common import ms2str, log_print, LogLevel, time_stat
from testutils import TestResult, parse_result


def parse_filename(name: str) -> (str, str, str, int):
    parts = name.split("_")
    if len(parts) > 4:
        p0 = "_".join(parts[:-3])
        parts = [p0] + parts[-3:]
    model = parts[0]
    version = parts[1]
    renderer = parts[2].upper()
    pass_num = int(parts[3][4:])
    return model, version, renderer, pass_num


def run():
    basedir = os.getcwd()
    now = time.strftime('%Y-%m-%d_%H-%M-%S')
    log_dir = os.path.join(basedir, 'log')
    out_dir = os.path.join(basedir, 'out')
    out_file = os.path.join(out_dir, now + ".csv")

    results = {}
    for file in sorted(os.listdir(log_dir)):
        filename = os.path.splitext(file)
        if filename[1] != "log":
            continue

        model, ver, renderer, pass_num = parse_filename(filename[0])
        config = (model, ver, renderer)

        with open(os.path.join(log_dir, file)) as src:
            data = src.read()
        it, rt = parse_result(data)

        log_print(LogLevel.I, " ".join([model, ver, renderer, ms2str(rt)]))
        if it > INIT_THRESHOLD:
            log_print(LogLevel.W, f"Kernel init took {it} ms, invalid result!")
            continue

        if config not in results:
            results[config] = []
        results[config].append(rt)

    log_print(LogLevel.I, "Writing output file")
    with open(out_file, 'w') as out:
        out.write(TestResult.header() + '\n')

        for config, times in results.items():
            rt, dev = time_stat(times)
            line = [*config, len(times), rt, ms2str(rt), f"{dev:.03f}"]
            line = ';'.join([str(s) for s in line])
            out.write(line + '\n')


if __name__ == '__main__':
    run()
