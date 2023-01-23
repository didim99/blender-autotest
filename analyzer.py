import os

from blender import init_threshold
from common import ms2str, log_print, LogLevel, parse_result


def parse_filename(name: str) -> (str, str, str):
    parts = name.split("_")
    if len(parts) > 4:
        p0 = "_".join(parts[:-3])
        parts = [p0] + parts[-3:]
    model = parts[0]
    version = parts[1]
    renderer = parts[2].upper()
    return model, version, renderer


def run():
    basedir = os.getcwd()
    log_dir = os.path.join(basedir, 'log')

    for file in sorted(os.listdir(log_dir)):
        filename = os.path.splitext(file)
        model, ver, renderer = parse_filename(filename[0])

        with open(os.path.join(log_dir, file)) as src:
            data = src.read()
        it, rt = parse_result(data)
        if it > init_threshold:
            log_print(LogLevel.W, f"Kernel init took {it} ms, invalid result!")
        log_print(LogLevel.I, " ".join([model, ver, renderer, ms2str(rt)]))


if __name__ == '__main__':
    run()
