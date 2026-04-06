# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""System compatibility checker for verifying hardware and software requirements."""

import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum

import carb
import omni.kit.app
import omni.platforminfo
from packaging.version import parse as parse_version

from .. import _compatibility_check


class Level(Enum):
    """Enumeration of compatibility check result levels."""

    UNMET: int = 0
    MINIMUM: int = 1
    GOOD: int = 2
    IDEAL: int = 3


@dataclass
class Result:
    """Data class representing a compatibility check result."""

    status: bool = False
    level: Level = Level.UNMET
    message: str = ""
    valid: bool = True  # whether the result is valid


class Checker:
    """System compatibility checker for verifying hardware and software requirements."""

    def __init__(self):
        """Initialize the compatibility checker."""
        self._nvidia_smi = Result()
        self._gpu_driver_version = Result()
        self._gpu_rtx = []
        self._gpu_vram = []
        self._cpu = Result()
        self._cpu_cores = Result()
        self._cpu_power_governor = Result()
        self._ram = Result()
        self._disk_storage = Result()
        self._operating_system = Result()
        self._display = Result()

        self._gpu_status = {}
        self._compatibility_check_status = True

    @property
    def compatibility_check_status(self):
        """Return the compatibility check status result."""
        return self._compatibility_check_status

    @property
    def operating_system(self):
        """Return the operating system result."""
        return self._operating_system

    @property
    def display(self):
        """Return the display result."""
        return self._display

    @property
    def nvidia_smi(self):
        """Return the nvidia smi result."""
        return self._nvidia_smi

    @property
    def gpu_driver_version(self):
        """Return the gpu driver version result."""
        return self._gpu_driver_version

    @property
    def gpu_rtx(self):
        """Return the gpu rtx result."""
        return self._gpu_rtx

    @property
    def gpu_vram(self):
        """Return the gpu vram result."""
        return self._gpu_vram

    @property
    def cpu(self):
        """Return the cpu result."""
        return self._cpu

    @property
    def cpu_cores(self):
        """Return the cpu cores result."""
        return self._cpu_cores

    @property
    def cpu_power_governor(self):
        """Return the cpu power governor result."""
        return self._cpu_power_governor

    @property
    def ram(self):
        """Return the ram result."""
        return self._ram

    @property
    def disk_storage(self):
        """Return the disk storage result."""
        return self._disk_storage

    def _set_compatibility_check_status(self, status: bool) -> None:
        self._compatibility_check_status = status and self._compatibility_check_status

    def _nvidia_smi_error(self) -> str:
        try:
            subprocess.check_output(["nvidia-smi"])
        except Exception as e:
            return str(e)
        return ""

    def _get_gpu_count(self) -> int:
        cmd = [
            "nvidia-smi",
            "--query-gpu=count",
            "--format=csv,noheader,nounits",
            "--id=0",
        ]
        try:
            raw_count = subprocess.check_output(cmd).decode().strip()
        except Exception as e:
            return -2
        try:
            return int(raw_count)
        except:
            return -1

    def check_nvidia_smi(self, spec: dict) -> None:
        """Check nvidia smi against specifications."""
        nvidia_smi_error = self._nvidia_smi_error()
        self._nvidia_smi.status = not len(nvidia_smi_error)
        self._nvidia_smi.message = nvidia_smi_error

    def check_driver_version(self, spec: dict) -> tuple[bool, str]:
        """Check driver version against specifications."""
        nvidia_smi_error = self._nvidia_smi_error()
        if nvidia_smi_error:
            self._gpu_driver_version.valid = False
            self._gpu_driver_version.message = nvidia_smi_error
            omni.kit.app.get_app().print_and_log(f"[WARNING] Unable to access GPU(s) configuration: {nvidia_smi_error}")
            self._set_compatibility_check_status(False)
            return

        # get spec
        driver_spec = {}
        for _spec in spec:
            if _spec["platform"] == sys.platform:
                driver_spec = _spec
                break

        if not driver_spec:
            self._gpu_driver_version.status = False
            return

        minimum = parse_version(driver_spec["minimum"])
        unsupported = [tuple([parse_version(v) for v in versions]) for versions in driver_spec["unsupported"]]

        # get driver version
        cmd = [
            "nvidia-smi",
            "--query-gpu=driver_version",
            "--format=csv,noheader,nounits",
            "--id=0",
        ]
        raw_version = subprocess.check_output(cmd).decode().strip()
        version = parse_version(raw_version)

        status = True
        message = f"{version}"

        # check minimum
        if version < minimum:
            status = False
            message = f"Below minimum {minimum}: {version}"
        # check unsupported
        for versions in unsupported:
            if version >= versions[0] and version <= versions[1]:
                status = False
                message = f"Unsupported {versions[0]} to {versions[1]}: {version} "

        omni.kit.app.get_app().print_and_log(f"  |-- Driver version [{'supported' if status else 'unsupported'}]")
        omni.kit.app.get_app().print_and_log(f"  |     |-- installed: {raw_version}")
        omni.kit.app.get_app().print_and_log(f"  |     |-- minimum: {minimum}")
        for versions in unsupported:
            omni.kit.app.get_app().print_and_log(f"  |     |-- unsupported: {versions[0]} - {versions[1]}")

        self._gpu_driver_version.status = status
        self._gpu_driver_version.message = message

        self._set_compatibility_check_status(status)

    def check_rtx_gpu(self, spec: dict) -> tuple[bool, str]:
        """Check rtx gpu against specifications."""
        num_gpus = self._get_gpu_count()
        self._gpu_rtx.clear()

        self._gpu_status["rtx"] = [True] * num_gpus

        for i in range(num_gpus):
            status = True
            message = ""

            # get GPU name and UUID
            cmd = [
                "nvidia-smi",
                "--query-gpu=gpu_name,uuid,pci.bus,pci.device_id,pci.sub_device_id",
                "--format=csv,noheader,nounits",
                f"--id={i}",
            ]
            raw_output = subprocess.check_output(cmd).decode().strip()
            gpu_name, gpu_uuid, pci_bus_id, device_id, sub_sys_id = raw_output.split(",")
            gpu_uuid = gpu_uuid.strip().lower().replace("-", "")
            pci_bus_id = pci_bus_id.strip().lower().replace("0x", "")
            device_id = device_id.strip().lower().replace("0x", "")
            sub_sys_id = sub_sys_id.strip().lower().replace("0x", "")

            # check for GPU name (naive)
            if "rtx" in gpu_name.lower():
                status = True
            elif "gtx" in gpu_name.lower():
                status = False
            # check for GPU (gpu.foundation)
            else:
                status = False
                # query info
                _interface = _compatibility_check.acquire_compatibility_check_interface()
                ret, rtx_gpu_info = _interface.get_rtx_gpu_info(False)  # don't create GPU Foundation
                if not ret:
                    carb.log_warn("Try creating GPU Foundation instance...")
                    ret, rtx_gpu_info = _interface.get_rtx_gpu_info(True)  # create GPU Foundation
                # parse info
                if ret:
                    for info in rtx_gpu_info:
                        if int(info.device_uuid, 16) and info.device_uuid.lower() in gpu_uuid:
                            status = info.raytracing_supported or info.raytracing_shader_feature
                        elif (
                            info.sub_sys_id.lower() in sub_sys_id
                            or (info.device_id + info.vendor_id).lower() in device_id
                        ):
                            status = info.raytracing_supported or info.raytracing_shader_feature

            omni.kit.app.get_app().print_and_log(f"  |-- GPU {i} [{'supported' if status else 'unsupported'}]")
            omni.kit.app.get_app().print_and_log(f"  |     |-- name: {gpu_name}")

            result = Result(status=status, message=f"{gpu_name}")
            self._gpu_rtx.append(result)

            self._gpu_status["rtx"][i] = status

    def check_vram(self, spec: dict) -> tuple[bool, str]:
        """Check vram against specifications."""
        num_gpus = self._get_gpu_count()
        self._gpu_vram.clear()

        self._gpu_status["vram"] = [True] * num_gpus

        for i in range(num_gpus):
            status = True
            level = Level.UNMET
            message = ""

            # get total memory
            cmd = [
                "nvidia-smi",
                "--query-gpu=memory.total",
                "--format=csv,noheader,nounits",
                f"--id={i}",
            ]
            raw_memory = subprocess.check_output(cmd).decode().strip()
            try:
                memory = round(int(raw_memory) * 0.00104858, 2)  # MiB -> GB
            except ValueError:
                memory = "N/A"

            # check total memory
            if memory == "N/A":
                level = Level.MINIMUM
                message = "cannot be identified"
            elif memory >= spec["ideal"]:
                level = Level.IDEAL
                message = "excellent"
            elif memory >= spec["good"]:
                level = Level.GOOD
                message = "good"
            elif memory >= spec["minimum"]:
                level = Level.MINIMUM
                message = "enough (more is recommended)"
            else:
                status = False
                level = Level.UNMET
                message = "not enough"

            omni.kit.app.get_app().print_and_log(f"  |-- GPU {i}: VRAM [{message}]")
            omni.kit.app.get_app().print_and_log(f"  |     |-- total: {memory} GB")
            omni.kit.app.get_app().print_and_log(f"  |     |-- minimum: {spec['minimum']} GB")

            result = Result(status=status, level=level, message=f"{memory}")
            self._gpu_vram.append(result)

            self._gpu_status["vram"][i] = status

        # set global GPU(s) status
        rtx_status = self._gpu_status.get("rtx", [])
        vram_status = self._gpu_status.get("vram", [])
        if len(rtx_status) != len(vram_status):
            carb.log_warn("Unable to check the system GPU(s) status")
            return
        global_status = False
        for rs, vs in zip(rtx_status, vram_status):
            global_status = rs and vs
            if global_status:
                break
        self._set_compatibility_check_status(global_status)

    def check_cpu(self, spec: dict) -> tuple[bool, str]:
        """Check cpu against specifications."""
        status = True

        # get CPU
        cpu_vendor = omni.platforminfo.ICpuInfo().get_vendor(0)
        cpu_pretty_name = omni.platforminfo.ICpuInfo().get_pretty_name(0)

        # check for CPU vendor
        if cpu_vendor.lower() == "genuineintel":
            status = True  # assume valid: no check for CPU specs
        elif cpu_vendor.lower() == "authenticamd":
            status = True  # assume valid: no check for CPU specs
        elif cpu_vendor.lower() == "arm":
            status = True  # assume valid: no check for CPU specs
        else:
            status = False

        omni.kit.app.get_app().print_and_log(f"  |-- CPU processor [{'supported' if status else 'unsupported'}]")
        omni.kit.app.get_app().print_and_log(f"  |     |-- name: {cpu_pretty_name}")

        self._cpu.status = status
        self._cpu.message = f"{cpu_pretty_name}"

        self._set_compatibility_check_status(status)

    def check_cpu_cores(self, spec: dict) -> tuple[bool, str]:
        """Check cpu cores against specifications."""
        status = True
        level = Level.UNMET
        message = ""

        # get number of cores
        cores = os.cpu_count()  # multiprocessing.cpu_count()

        # check total memory
        if cores >= spec["ideal"]:
            level = Level.IDEAL
            message = "excellent"
        elif cores >= spec["good"]:
            level = Level.GOOD
            message = "good"
        elif cores >= spec["minimum"]:
            level = Level.MINIMUM
            message = "enough (more is recommended)"
        else:
            status = False
            level = Level.UNMET
            message = "not enough"

        omni.kit.app.get_app().print_and_log(f"  |-- CPU cores [{message}]")
        omni.kit.app.get_app().print_and_log(f"  |     |-- total: {cores}")
        omni.kit.app.get_app().print_and_log(f"  |     |-- minimum: {spec['minimum']}")

        self._cpu_cores.status = status
        self._cpu_cores.level = level
        self._cpu_cores.message = f"{cores}"

        self._set_compatibility_check_status(status)

    def check_cpu_power_governor(self, spec: dict) -> tuple[bool, str]:
        """Check cpu power governor against specifications."""
        status = True
        level = Level.UNMET
        message = ""
        governors = set()
        mode = ""

        if not sys.platform.startswith("linux"):
            mode = "Not Available"
            status = False
            message = "CPU Governors are not supported on Windows"

        else:
            cpu_path = "/sys/devices/system/cpu/"
            try:
                cpu_entries = os.listdir(cpu_path)
            except (PermissionError, FileNotFoundError) as e:
                level = Level.UNMET
                message = f"Cannot access CPU governor directory: {str(e)}"
                omni.kit.app.get_app().print_and_log(f"  |-- CPU power governor [{message}]")
                self._cpu_power_governor.status = False
                self._cpu_power_governor.level = level
                self._cpu_power_governor.message = ""
                return

            for entry in cpu_entries:
                if entry.startswith("cpu") and entry[3:].isdigit():  # Filter CPU directories
                    path = f"{cpu_path}{entry}/cpufreq/scaling_governor"
                    try:
                        with open(path, "r") as file:
                            governor = file.read().strip()
                            governors.add(governor)
                    except FileNotFoundError:
                        level = Level.UNMET
                        message = "CPU power governor file not found for some cores"
                        break

            # If all cores have the same governor
            if status and len(governors) == 1:
                governor = governors.pop()  # Get the single governor setting
                mode = governor.capitalize()
                if governor == "performance" or governor == "schedutil":
                    level = Level.IDEAL
                    message = "ideal"
                elif governor == "ondemand" or governor == "conservative":
                    level = Level.GOOD
                    message = "performance may be degraded - 'Performance' is recommended"
                elif governor == "powersave":
                    level = Level.MINIMUM
                    message = "performance may be degraded - 'Performance' is recommended"
                else:
                    mode = "Unknown Governor"
                    message = "Unknown CPU governor selected"
                    status = False

            # Multiple governor settings found for different cores
            elif status and len(governors) > 1:
                level = Level.MINIMUM
                mode = "Inconsistent Governors Found"
                message = "Multiple CPU governors found - 'Performance' is recommended"

        omni.kit.app.get_app().print_and_log(f"  |-- CPU power governor [{message}]")
        omni.kit.app.get_app().print_and_log(f"  |     |-- governor(s): {mode}")

        self._cpu_power_governor.status = status
        self._cpu_power_governor.level = level
        self._cpu_power_governor.message = mode

    def check_ram(self, spec: dict) -> tuple[bool, str]:
        """Check ram against specifications."""
        status = True
        level = Level.UNMET
        message = ""

        # get RAM size
        memory = omni.platforminfo.IMemoryInfo().total_physical_memory
        memory = round(memory * 1e-9, 2)  # byte -> GB

        # check total memory
        if memory >= spec["ideal"]:
            level = Level.IDEAL
            message = "excellent"
        elif memory >= spec["good"]:
            level = Level.GOOD
            message = "good"
        elif memory >= spec["minimum"]:
            level = Level.MINIMUM
            message = "enough (more is recommended)"
        else:
            status = False
            level = Level.UNMET
            message = "not enough"

        omni.kit.app.get_app().print_and_log(f"  |-- RAM [{message}]")
        omni.kit.app.get_app().print_and_log(f"  |     |-- total: {memory} GB")
        omni.kit.app.get_app().print_and_log(f"  |     |-- minimum: {spec['minimum']} GB")

        self._ram.status = status
        self._ram.level = level
        self._ram.message = f"{memory}"

        self._set_compatibility_check_status(status)

    def check_operating_system(self, operating_system: dict) -> tuple[bool, str]:
        """Check operating system against specifications."""
        # get OS name and version
        os_name = [omni.platforminfo.IOsInfo().distro_name.lower(), platform.system().lower()]
        os_pretty_name = omni.platforminfo.IOsInfo().pretty_name
        os_version = omni.platforminfo.IOsInfo().os_version
        os_version = f"{os_version.major}.{os_version.minor}"

        # check OS
        status = False
        for _os in operating_system:
            if _os["name"].lower() in os_name:
                for version in _os["versions"]:
                    if parse_version(version) == parse_version(os_version):
                        status = True
                        break

        omni.kit.app.get_app().print_and_log(f"  |-- Operating system [{'supported' if status else 'unsupported'}]")
        omni.kit.app.get_app().print_and_log(f"  |     |-- name and version: {os_pretty_name}")

        self._operating_system.status = status
        self._operating_system.message = os_pretty_name

        self._set_compatibility_check_status(status)

    def check_storage(self, spec: dict) -> tuple[bool, str]:
        """Check storage against specifications."""
        status = True
        level = Level.UNMET
        message = ""

        # get partitions
        if sys.platform == "linux":
            cmd = "df -l -x tmpfs -x efivarfs -x vfat --output=target".split(" ")
            raw_partitions = subprocess.check_output(cmd).decode().strip()
            partitions = raw_partitions.split("\n")[1:]
        else:
            partitions = [f"{chr(x)}:" for x in range(65, 91) if os.path.exists(f"{chr(x)}:")]

        # get available storage
        storage = 0
        for partition in partitions:
            disk_usage = shutil.disk_usage(partition)
            storage += disk_usage.free

        storage = round(storage * 1e-9, 2)

        # check available storage
        if storage >= spec["ideal"]:
            level = Level.IDEAL
            message = "excellent"
        elif storage >= spec["good"]:
            level = Level.GOOD
            message = "good"
        elif storage >= spec["minimum"]:
            level = Level.MINIMUM
            message = "enough (more is recommended)"
        else:
            status = False
            level = Level.UNMET
            message = "not enough"

        omni.kit.app.get_app().print_and_log(f"  |-- Storage [{message}]")
        omni.kit.app.get_app().print_and_log(f"  |     |-- total available: {storage} GB")
        omni.kit.app.get_app().print_and_log(f"  |     |-- minimum: {spec['minimum']} GB")

        self._disk_storage.status = status
        self._disk_storage.level = level
        self._disk_storage.message = f"{storage}"

    def check_display(self) -> tuple[bool, str]:
        """Check display against specifications."""
        status = False
        message = ""

        # get the number of displays
        display_count = omni.platforminfo.IDisplayInfo().display_count

        # check displays
        if display_count:
            status = True
            message = f"available: {display_count} display(s)"
            self._display.message = "Visualization available on-site"
        else:
            message = "no display was detected, visit the following link for information \
on the different livestreaming methods to view headless application instances: \
docs.omniverse.nvidia.com/isaacsim/latest/installation/manual_livestream_clients.html"
            self._display.message = "Only remote visualization via streaming"

        omni.kit.app.get_app().print_and_log(f"  |-- Display [{message}]")

        self._display.status = status
