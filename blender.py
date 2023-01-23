
"""
    If kernel initialization time took over 100ms
    it seems to be first time rendering with this
    engine, skip this result and run test again
"""
init_threshold = 100


class BlenderVer:
    V2_79 = 27900
    V2_80 = 28000
    V2_91 = 29100


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
