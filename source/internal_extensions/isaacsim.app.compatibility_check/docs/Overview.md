```{csv-table}
**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`
```

# Overview

The isaacsim.app.compatibility_check extension verifies that the host system meets hardware and software requirements for running Isaac Sim. It checks GPU, CPU, memory, storage, driver, and OS compatibility, reporting results at four levels: unmet, minimum, good, and ideal.

## Checks Performed

- **GPU**: Verifies nvidia-smi availability, RTX ray-tracing support, and VRAM capacity (minimum 10 GB, ideal 48 GB)
- **GPU Driver**: Validates driver version against minimum requirements (Linux: 535.161+, Windows: 537.58+)
- **CPU**: Checks vendor, core count (minimum 4, ideal 16), and power governor settings on Linux
- **RAM**: Validates system memory (minimum 32 GB, ideal 128 GB)
- **Storage**: Checks available disk space (minimum 50 GB, ideal 1 TB)
- **OS**: Verifies operating system compatibility (Ubuntu 22.04/24.04, Windows 10/11)
- **Display**: Detects display availability for GUI-based workflows
