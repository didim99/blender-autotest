import os
import platform
import subprocess
from typing import Dict


class TestConfig:
    modelName: str
    modelPath: str
    versionName: str
    execPath: str
    logDir: str
    tempDir: str

    logPath: str

    def build(self) -> None:
        name = f"{self.modelName}_{self.versionName}"
        self.logPath = os.path.join(self.logDir, name)

def find_blender(basedir: str) -> Dict[str, str]:
    env = platform.system().lower()
    bin_dir = os.path.join(basedir, 'bin', 'blender', env)
    bin_name = 'blender.exe' if env == 'windows' else 'blender'
    versions = {}

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
        versions[version] = exe
        print(f"Found Blender v{version} in {exe}")

    return versions

def find_models(basedir: str) -> Dict[str, str]:
    modeldir = os.path.join(basedir, 'models')
    models = {}

    for file in os.listdir(modeldir):
        name = os.path.splitext(file)
        if name[1] != '.blend':
            continue

        models[name[0]] = os.path.join(modeldir, file)
        print(f"Found model: {file}")

    return models

def run_test(config: TestConfig) -> None:
    # for renderer in ['CPU', 'CUDA', 'OPTIX']:
    for renderer in ['OPTIX']:
        log_file = f"{config.logPath}_{renderer.lower()}.log"
        out_file = os.path.join(config.tempDir, "render-")

        args = [
            config.execPath,
            '--background', config.modelPath,
            '--render-output', out_file,
            '--render-frame', '1', '--',
            '--cycles-device', renderer
        ]

        print(f"Rendering with {renderer} engine...")
        result = subprocess.run(args, capture_output=True,
                                check=False)

        if result.returncode != 0:
            print("Render failed!")
            print(result.stdout)
            print(result.stderr)
            continue

        with open(log_file, 'wb') as log:
            log.write(result.stdout)

def run():
    basedir = os.getcwd()
    log_dir = os.path.join(basedir, 'log')
    tmp_dir = os.path.join(basedir, 'tmp')
    versions = find_blender(basedir)
    models = find_models(basedir)

    for d in log_dir, tmp_dir:
        if not os.path.isdir(d):
            os.mkdir(d)

    for model, model_path in models.items():
        for version, exe_path in versions.items():
            config = TestConfig()
            config.modelName = model
            config.versionName = version
            config.modelPath = model_path
            config.execPath = exe_path
            config.tempDir = tmp_dir
            config.logDir = log_dir
            config.build()

            print(f"Testing model {model} with Blender v{version}")
            run_test(config)


if __name__ == '__main__':
    run()
