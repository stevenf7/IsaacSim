# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import datetime
import inspect
import os
import shutil
import subprocess
from typing import Tuple

import carb
import nvsmi
import omni
import psutil
import yaml

### need to check copyrights: https://www.programcreek.com/python/?code=SummaLabs%2FDLS%2FDLS-master%2Fapp%2Fbackend%2Fenv%2Fhardware.py

# Query CPU Info from OS
def get_cpu_info():
    cpu_info = {"cpu cores": psutil.cpu_count(), "cpu RAM": psutil.virtual_memory()[3] / 1000000}
    return cpu_info


def get_gpu_info():
    output_to_list = lambda x: x.decode("ascii").split("\n")[:-1]
    bash_command = "nvidia-smi --query-gpu=name,count,driver_version --format=csv"
    try:
        info_out = output_to_list(subprocess.check_output(bash_command.split(), stderr=subprocess.STDOUT))[1].split(",")
        gpu_info = {"name": info_out[0].strip(), "num_gpu": info_out[1].strip(), "driver_version": info_out[2].strip()}
    except OSError:
        gpu_info = {"error": "GPU device is not available"}

    return gpu_info


def get_memory_stats() -> dict:
    """Returns dictionary with memory usage staticstics in MB for GPU and Host memory

    Returns:
        dict: dictionary with memory usage statistics. The "Total" key contains totals for each category
    """
    memory_usage = {}

    process_id = os.getpid()
    process = psutil.Process(process_id)
    RAM = process.memory_info().rss * 1e-6  # byte to mb
    memory_usage["System Memory"] = {}
    memory_usage["System Memory"]["RAM"] = RAM
    gpu_processes = nvsmi.get_gpu_processes()
    VRAM = 0
    for gpu_process in gpu_processes:
        if gpu_process.pid == process_id:
            VRAM = gpu_process.used_memory
            break
    memory_usage["System Memory"]["VRAM"] = VRAM

    memory_usage["Total"] = {}
    stats_interface = omni.stats.get_stats_interface()
    scopes = stats_interface.get_scopes()
    for scope in scopes:
        stat_dict = {}
        scope_id = scope["scopeId"]
        stats = stats_interface.get_stats(scope_id)
        total = 0
        for s in stats:
            stat_dict[s["name"]] = s["value"]
            total += s["value"]

        memory_usage[scope["name"]] = stat_dict
        memory_usage["Total"][scope["name"]] = total

    return memory_usage


def get_hardware_stats() -> Tuple[float, float, float, float, float, float]:
    from omni.hydra.engine.stats import get_device_info, get_mem_stats  # type: ignore

    # CPU.
    cpu_load = round(psutil.cpu_percent(3), 2)  # %

    # RAM used for kit.exe.
    process = psutil.Process(os.getpid())
    # Physical Memory Working Set
    rss_mb = process.memory_info().rss / (1024**2)  # MB
    rss = round(rss_mb / 1024, 3)  # GB
    # Virtual Memory Private Bytes
    vms_mb = process.memory_info().vms / (1024**2)  # MB
    vms = round(vms_mb / 1024, 3)  # GB
    # Unique Set Size
    uss_mb = process.memory_full_info().uss / (1024**2)  # MB
    uss = round(uss_mb / 1024, 3)  # GB

    # GPU from profiler window.
    memStat_sort = True
    memStat_detail = False
    tracked_gpu_memory = 0.0
    memStat_nodes = get_mem_stats(memStat_detail)
    # Sort nodes in descending order based on time if requested
    if memStat_sort is True:
        memStat_nodes = sorted(memStat_nodes, key=lambda node: node["size"], reverse=True)
    for node in memStat_nodes:
        if node["category"] == "Total Physical GPU Memory":
            tracked_gpu_memory = round(node["size"] / 1024, 3)  # MB to GB

    devices = get_device_info()
    device = devices[0]
    dedicated_gpu_memory = round(device["usage"] / 1073741824, 3)  # bytes to GB

    return cpu_load, rss, vms, uss, tracked_gpu_memory, dedicated_gpu_memory


def log_stamp(file_path):
    memory_stats = get_memory_stats()
    memory_stats = {"System Memory": memory_stats["System Memory"]}

    # Key log entry with timestamp
    timestamp = str(datetime.datetime.now())
    memory_stats = {timestamp: memory_stats}

    # Append to the end of log
    with open(file_path, "a") as f:
        yaml.safe_dump(memory_stats, f)
    f.close()

    print("\nlogging time and memory stamp: ", memory_stats)


def log_header():
    test_name = inspect.stack()[1].function
    test_folder = test_name[15:]
    test_time = datetime.datetime.now().strftime("%Y-%m-%d-%Hh%M")

    # log file
    settings = carb.settings.get_settings()
    reset_log_on_start = settings.get("/exts/omni.isaac.benchmarks/resetLogOnStart")
    log_file_path = carb.tokens.get_tokens_interface().resolve("${logs}") + "/isaac_benchmarks/log/log.yaml"
    omni.kit.app.get_app().print_and_log(f"[omni.isaac.benchmarks] Logging to file: {log_file_path}")

    # Create log path, if needed
    log_path = os.path.dirname(log_file_path)
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)

    # Create log file, if needed
    create_new_file = reset_log_on_start or not os.path.exists(log_file_path)
    if create_new_file:
        open(log_file_path, "w").close()

    # data file
    data_file_path = (
        carb.tokens.get_tokens_interface().resolve("${logs}")
        + "/isaac_benchmarks/"
        + test_folder
        + "/"
        + test_time
        + ".yaml"
    )
    omni.kit.app.get_app().print_and_log(f"[omni.isaac.benchmarks] Benchmark Data saved to file: {data_file_path}")

    # Create data path, if needed
    data_path = os.path.dirname(data_file_path)
    if not os.path.exists(data_path):
        os.makedirs(data_path, exist_ok=True)

    ## if you want to delete all previous tests in this folder
    # if os.path.exists(data_path):
    #     shutil.rmtree(data_path)
    # os.makedirs(data_path, exist_ok=True)

    # Create data file
    if not os.path.exists(data_file_path):
        open(data_file_path, "w").close()

    test_info = {"Test Name": test_name, "Test Time": test_time}
    gpu_info = get_gpu_info()
    cpu_info = get_cpu_info()

    # write data header
    with open(data_file_path, "a") as f:
        yaml.safe_dump(test_info, f)
        yaml.safe_dump(cpu_info, f)
        yaml.safe_dump(gpu_info, f)

    f.close()

    return data_path, data_file_path
