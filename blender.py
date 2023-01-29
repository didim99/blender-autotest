from __future__ import annotations


"""
    If kernel initialization time took over 100ms
    it seems to be first time rendering with this
    engine, skip this result and run test again
"""
INIT_THRESHOLD = 100


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


class ModelType:
    CPU = 'cpu'
    GPU = 'gpu'


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
