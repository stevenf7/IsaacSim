# Public API for module isaacsim.app.compatibility_check:

## Classes

- class Extension(omni.ext.IExt)
  - def on_startup(self, ext_id: str)
  - def on_shutdown(self)

# Public API for module isaacsim.app.compatibility_check.impl.compatibility_checker:

## Classes

- class Level(Enum)
  - UNMET: int
  - MINIMUM: int
  - GOOD: int
  - IDEAL: int

- class Result
  - status: bool
  - level: Level
  - message: str
  - valid: bool

- class Checker
  - def __init__(self)
  - [property] def compatibility_check_status(self) -> bool
  - [property] def operating_system(self) -> Result
  - [property] def display(self) -> Result
  - [property] def nvidia_smi(self) -> Result
  - [property] def gpu_driver_version(self) -> Result
  - [property] def gpu_rtx(self) -> list[Result]
  - [property] def gpu_vram(self) -> list[Result]
  - [property] def cpu(self) -> Result
  - [property] def cpu_cores(self) -> Result
  - [property] def cpu_power_governor(self) -> Result
  - [property] def ram(self) -> Result
  - [property] def disk_storage(self) -> Result
  - def check_nvidia_smi(self, spec: dict)
  - def check_driver_version(self, spec: dict)
  - def check_rtx_gpu(self, spec: dict)
  - def check_vram(self, spec: dict)
  - def check_cpu(self, spec: dict)
  - def check_cpu_cores(self, spec: dict)
  - def check_cpu_power_governor(self, spec: dict)
  - def check_ram(self, spec: dict)
  - def check_operating_system(self, operating_system: dict)
  - def check_storage(self, spec: dict)
  - def check_display(self)
