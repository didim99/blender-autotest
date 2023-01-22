from __future__ import annotations

import os
import platform
import re
import statistics
import subprocess
import time
from typing import List
from subprocess import CompletedProcess


def str2ms(ts: str) -> int:
    ts = reversed(ts.split(':'))
    res = 0

    for r, t in enumerate(ts):
        if '.' in t:
            t = t.split('.')
            t = int(t[0]) * 1000 + int(t[1])
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


class ModelType:
    CPU = 'cpu'
    GPU = 'gpu'


class DeviceType:
    CPU = 'CPU'
    CUDA = 'CUDA'
    OPTIX = 'OPTIX'

    @staticmethod
    def all():
        return [
            DeviceType.CPU,
            DeviceType.CUDA,
            DeviceType.OPTIX
        ]

class BlenderVer:
    V2_79 = 27900
    V2_80 = 28000
    V2_91 = 29100


class BlenderExe(object):
    versionName: str = None
    versionCode: int = None
    execPath: str = None

    def __init__(self, version: str, exe: str):
        self.versionName = version
        self.execPath = exe
        self.parse_version()

    def parse_version(self):
        ver = self.versionName.split('.')
        ver = [int(v) for v in ver]
        self.versionCode = ver[0] * 10000
        if len(ver) > 1:
            self.versionCode += ver[1] * 100
        if len(ver) > 2:
            self.versionCode += ver[2]

    def ver(self) -> str:
        return f"Blender v{self.versionName}"

    def __lt__(self, other: BlenderExe):
        return self.versionCode < other.versionCode

    def __repr__(self):
        return f"{self.ver()} [{self.versionCode}] in {self.execPath}"


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

    tempDir: str = None
    logPath: str = None
    outFile: str = None

    def __init__(self, blender: BlenderExe,
                 model: TestModel, passes: int = 3):
        self.passes = passes
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
    time: int = None

    def __init__(self, config: TestConfig, renderer: str, time: int):
        self.model = config.model
        self.blender = config.blender
        self.passes = config.passes
        self.renderer = renderer
        self.time = time

    def __str__(self):
        return ";".join([
            self.model.name,
            self.blender.versionName,
            self.renderer,
            str(self.passes),
            str(self.time),
            ms2str(self.time)
        ])

    @staticmethod
    def header():
        return ";".join([
            'model',
            'version',
            'renderer',
            'passes',
            'time_ms',
            'time'
        ])


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
        print(f"[INFO] Found {version}")

    return sorted(versions)


def find_models(basedir: str) -> List[TestModel]:
    modeldir = os.path.join(basedir, 'models')
    models = {}

    for file in os.listdir(modeldir):
        filename = os.path.splitext(file)
        if filename[1] != '.blend':
            continue

        name = filename[0][:-4]
        _type = filename[0][-3:].lower()
        path = os.path.join(modeldir, file)

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

        print(f"[INFO] Found {model}")

    return sorted([*models.values()])


def parse_result(result: CompletedProcess) -> int:
    stdout = str(result.stdout, 'utf-8')
    stdout = reversed(stdout.split('\n'))

    bound = False
    time_str = None
    for line in stdout:
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
        print(str(result.stdout, 'utf-8'))
        raise RuntimeError('failed to find rendering time')

    m = re.search(r"Time:\s(?P<total>[\d.:]+)\s\(Saving:\s(?P<save>[\d.:]+)\)",
                  time_str)

    total = str2ms(m.group('total'))
    save = str2ms(m.group('save'))
    render = total - save
    return render


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
    print(f"[INFO] Testing {config.model} with {config.blender.ver()}")

    results = []
    for renderer in DeviceType.all():
        if renderer == DeviceType.OPTIX \
            and config.blender.versionCode < BlenderVer.V2_91:
            print(f"[WARN] Unable to run" +
                  f" {config.blender.ver()} in {renderer} mode")
            continue

        if renderer != DeviceType.CPU \
            and config.blender.versionCode < BlenderVer.V2_91 \
            and config.model.pathGpu is None:
            print(f"[WARN] Unable to test {config.model} with" +
                  f" {config.blender.ver()} in {renderer} mode")
            continue

        args = [
            config.blender.execPath,
            '--background', config.model.pathCpu,
            '--render-output', config.outFile,
            '--render-frame', '1', '--',
            '--cycles-device', renderer
        ]

        times = []
        for p in range(config.passes):
            log_file = f"{config.logPath}_{renderer.lower()}_pass{p+1:02d}.log"

            print(f"[VERB] Rendering with {renderer} engine (pass {p+1})...")
            result = subprocess.run(args, capture_output=True,
                                    check=False)

            if result.returncode != 0:
                print("[WARN] " + parse_error(result))
                break

            with open(log_file, 'wb') as log:
                log.write(result.stdout)

            rt = parse_result(result)
            times.append(rt)

        rt = int(round(statistics.fmean(times)))
        print(f"[INFO] Test finished, average time: {ms2str(rt)}")
        result = TestResult(config, renderer, rt)
        results.append(result)

    return results


def run():
    test_passes = 3
    basedir = os.getcwd()
    log_dir = os.path.join(basedir, 'log')
    tmp_dir = os.path.join(basedir, 'tmp')
    out_dir = os.path.join(basedir, 'out')
    versions = find_blender(basedir)
    models = find_models(basedir)

    for d in log_dir, tmp_dir, out_dir:
        if not os.path.isdir(d):
            os.mkdir(d)

    now = time.strftime('%Y-%m-%d_%H-%M-%S.csv')
    out_file = os.path.join(out_dir, now)
    with open(out_file, 'a') as out:
        out.write(TestResult.header() + '\n')

    for model in models:
        for exe in versions:
            config = TestConfig(exe, model, test_passes)
            config.build(tmp_dir, log_dir)
            result = run_test(config)

            with open(out_file, 'a') as out:
                result = '\n'.join([str(r) for r in result])
                out.write(result + '\n')

    print(f"[INFO] Deleting temporary files")
    for file in os.listdir(tmp_dir):
        os.remove(os.path.join(tmp_dir, file))
    os.rmdir(tmp_dir)


if __name__ == '__main__':
    run()
