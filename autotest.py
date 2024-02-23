import os
import platform
import subprocess
import time
from typing import List
from subprocess import CompletedProcess
from zipfile import ZipFile

from blender import INIT_THRESHOLD, DeviceType, ModelType, BlenderVer, BlenderExe
from common import ms2str, log_setup, log_print, LogLevel, time_stat, freq_stat
from testutils import TestModel, TestConfig, TestResult, parse_result

try:
    from cpuinfo import get_cpu_info
    from hwmeters import CPUFreqWatcher
except ImportError:
    get_cpu_info = None
    CPUFreqWatcher = None


def find_blender(basedir: str) -> List[BlenderExe]:
    env = platform.system().lower()
    bin_dir = os.path.join(basedir, 'bin', 'blender', env)
    bin_name = 'blender.exe' if env == 'windows' else 'blender'
    versions = []

    for vd in os.listdir(bin_dir):
        exe = os.path.join(bin_dir, vd, bin_name)
        if not os.path.isfile(exe) \
                or not os.access(exe, os.X_OK):
            continue

        result = subprocess.run([exe, '--version'],
                                capture_output=True,
                                check=True)

        if not result.stdout:
            continue

        line = result.stdout.split(b'\n')[0].strip()
        line = str(line, 'utf-8').split(' ')
        if line[0].lower() != 'blender':
            continue

        version = line[1]
        version = BlenderExe(version, exe)
        versions.append(version)
        log_print(LogLevel.I, f"Found {version}")

    return sorted(versions)


def find_models(basedir: str) -> List[TestModel]:
    model_dir = os.path.join(basedir, 'models')
    models = {}

    for file in os.listdir(model_dir):
        filename = os.path.splitext(file)
        if filename[1] != '.blend':
            continue

        name = filename[0][:-4]
        _type = filename[0][-3:].lower()
        path = os.path.join(model_dir, file)

        if name in models:
            model = models[name]
        else:
            model = TestModel(name)
            models[name] = model

        if _type == ModelType.CPU:
            model.pathCpu = path
        elif _type == ModelType.GPU:
            model.pathGpu = path
        else:
            model.pathCpu = path

        log_print(LogLevel.I, f"Found {model}")

    return sorted([*models.values()])


def parse_error(result: CompletedProcess) -> str:
    error = "unknown error"

    if result.stderr:
        stderr = str(result.stderr, 'utf-8')
        error = stderr[:stderr.index('\n')]
    else:
        stdout = str(result.stdout, 'utf-8')
        stdout = reversed(stdout.split('\n'))
        for line in stdout:
            if line.startswith("Error"):
                error = line

    return "Render failed: " + error


def run_test(config: TestConfig) -> List[TestResult]:
    log_print(LogLevel.I, f"Testing {config.model} with {config.blender.ver()}")

    monitor = CPUFreqWatcher() if config.monitor_cpu else None
    results = []

    for renderer in DeviceType.all():
        if renderer == DeviceType.OPTIX \
                and config.blender.versionCode < BlenderVer.V2_91:
            log_print(LogLevel.W, f"Unable to run" +
                      f" {config.blender.ver()} in {renderer} mode")
            continue

        if renderer != DeviceType.CPU \
                and config.blender.versionCode < BlenderVer.V2_91 \
                and config.model.pathGpu is None:
            log_print(LogLevel.W, f"Unable to test {config.model} with" +
                      f" {config.blender.ver()} in {renderer} mode")
            continue

        cpu_monitoring = monitor is not None and renderer == DeviceType.CPU

        args = [
            config.blender.execPath,
            '--background', config.model.pathCpu,
            '--render-output', config.outFile,
            '--render-frame', '1', '--',
            '--cycles-device', renderer
        ]

        p = 1
        times = []
        freqs = []
        while p <= config.passes:
            log_file = f"{config.logPath}_{renderer.lower()}_pass{p:02d}.log"
            freq_file = f"{config.logPath}_{renderer.lower()}_pass{p:02d}_cpufreq.csv"

            if cpu_monitoring:
                monitor.run()

            log_print(LogLevel.V, f"Rendering with {renderer} engine (pass {p})...")
            result = subprocess.run(args, capture_output=True,
                                    check=False)

            if cpu_monitoring:
                monitor.stop()
                freq = monitor.get_stat()
                log_print(LogLevel.V, f"CPU frequency (min/max/avg): "
                                      f"{freq.min:.2f}/{freq.max:.2f}/{freq.avg:.2f} MHz")
                freqs.append(freq)
                monitor.write_csv(freq_file)

            if result.returncode != 0:
                log_print(LogLevel.W, parse_error(result))
                break

            it, rt = parse_result(result.stdout)
            if it > INIT_THRESHOLD:
                log_print(LogLevel.W, f"Kernel init took {it}ms, invalid result!")
                continue

            with open(log_file, 'wb') as log:
                log.write(result.stdout)

            times.append(rt)
            p += 1

        if len(times) < 1:
            continue

        rt, dev = time_stat(times)
        dev_percent = dev / rt * 100
        log_print(LogLevel.I, f"Test finished, average time: {ms2str(rt)}, "
                  + f"stddev: {dev:.03f} ms ({dev_percent:.02f}%)")
        result = TestResult(config, renderer, times)

        if cpu_monitoring:
            freq, fdev = freq_stat([freq.avg for freq in freqs])
            fdev_percent = fdev / freq * 100
            log_print(LogLevel.I, f"Average CPU frequency: {freq:.2f} MHz, "
                      + f"stddev: {fdev:.03f} MHz ({fdev_percent:.02f}%)")
            result.add_freq_stat(freqs)

        results.append(result)

    return results


def run():
    test_passes = 3
    monitor_cpu = CPUFreqWatcher is not None
    basedir = os.getcwd()
    log_dir = os.path.join(basedir, 'log')
    tmp_dir = os.path.join(basedir, 'tmp')
    out_dir = os.path.join(basedir, 'out')

    for d in log_dir, tmp_dir, out_dir:
        if not os.path.isdir(d):
            os.mkdir(d)

    now = time.strftime('%Y-%m-%d_%H-%M-%S')
    log_file = os.path.join(out_dir, now + ".log")
    out_file = os.path.join(out_dir, now + ".csv")
    log_setup(log_file)

    versions = find_blender(basedir)
    if len(versions) == 0:
        log_print(LogLevel.E, "No any version of Blender found, aborting")
    models = find_models(basedir)
    if len(versions) == 0:
        log_print(LogLevel.E, "No any test model found, aborting")

    if get_cpu_info is not None:
        cpu_model = get_cpu_info()['brand_raw']
        log_print(LogLevel.I, f"Found CPU: {cpu_model}")
    else:
        log_print(LogLevel.W, f"CPU monitoring is not available, "
                              f"possible missing dependencies")

    with open(out_file, 'a') as out:
        out.write(TestResult.header() + '\n')

    for model in models:
        for exe in versions:
            config = TestConfig(exe, model, test_passes, monitor_cpu)
            config.build(tmp_dir, log_dir)
            result = run_test(config)

            with open(out_file, 'a') as out:
                result = '\n'.join([str(r) for r in result])
                out.write(result + '\n')

    log_print(LogLevel.I, "Creating result archive")
    zip_file = os.path.join(out_dir, now + ".zip")
    with ZipFile(zip_file, 'w') as archive:
        archive.write('log')
        for file in os.listdir(log_dir):
            path = os.path.join(log_dir, file)
            archive.write(path, os.path.join('log', file))
        archive.write('out')
        archive.write(out_file, os.path.join('out', now + ".csv"))
        archive.write(log_file, os.path.join('out', now + ".log"))

    log_print(LogLevel.I, "Deleting temporary files")
    for file in os.listdir(tmp_dir):
        os.remove(os.path.join(tmp_dir, file))
    os.rmdir(tmp_dir)


if __name__ == '__main__':
    run()
