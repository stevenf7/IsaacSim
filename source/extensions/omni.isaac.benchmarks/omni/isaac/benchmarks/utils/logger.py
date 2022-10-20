# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni
import carb

import datetime
import inspect
import psutil, os, shutil
import yaml
import nvsmi
import subprocess

### need to check copyrights: https://www.programcreek.com/python/?code=SummaLabs%2FDLS%2FDLS-master%2Fapp%2Fbackend%2Fenv%2Fhardware.py

# Query CPU Info from OS
def get_cpu_info():
    empty_info = {"id": "cpu", "name": "-", "cores": "-", "cache": "-"}
    try:
        output = execute_bash_command("cat /proc/cpuinfo")
        lines = output.split("\n")
        if len(lines) > 12:
            cpu = lines[4].split(":")[1]
            cores = lines[12].split(":")[1]
            cache = lines[8].split(":")[1]
            cpu_info = {"id": "cpu", "name": cpu, "cores": cores, "cache": cache}
        else:
            cpu_info = empty_info
        return cpu_info
    except OSError:
        return empty_info


def execute_bash_command(cmd):
    tenv = os.environ.copy()
    tenv["LC_ALL"] = "C"
    bash_command = cmd
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE, env=tenv)
    return process.communicate()[0]


def get_gpu_info():
    gpu_info = []
    try:
        bash_command = "nvidia-smi --query-gpu=index,name,uuid,memory.total,memory.free,memory.used,count,utilization.gpu,utilization.memory --format=csv"
        output = execute_bash_command(bash_command)
        print("outputs", output)
        lines = output.split("\n")
        lines.pop(0)
        for l in lines:
            tokens = l.split(", ")
            if len(tokens) > 6:
                gpu_info.append(
                    {
                        "id": tokens[0],
                        "name": tokens[1],
                        "mem": tokens[3],
                        "cores": tokens[6],
                        "mem_free": tokens[4],
                        "mem_used": tokens[5],
                        "util_gpu": tokens[7],
                        "util_mem": tokens[8],
                    }
                )
    except OSError:
        # logger.info("GPU device is not available")
        pass

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


def log_stamp(file_path):
    memory_stats = get_memory_stats()
    memory_stats = {"System Memory": memory_stats["System Memory"]}

    # Key log entry with timestamp
    timestamp = str(datetime.datetime.now())
    memory_stats = {timestamp: memory_stats}

    # Append to the end of log
    with open(file_path, "a") as f:
        yaml.safe_dump(memory_stats, f)

    print("\nlogging time and memory stamp: ", memory_stats)


def log_header():
    test_name = inspect.stack()[1].function
    test_folder = test_name[15:]
    test_time = datetime.datetime.now().strftime("%Y-%m-%d-%Hh%M")

    # get test hardware info
    # gpu_info = get_gpu_info()
    # num_gpus = len(gpu_info["id"])
    # gpu_name = gpu_info["name"]

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
    if os.path.exists(data_path):
        shutil.rmtree(data_path)
    os.makedirs(data_path, exist_ok=True)

    # Create data file
    if not os.path.exists(data_file_path):
        open(data_file_path, "w").close()

    test_info = {"Test Name": test_name, "Test Time": test_time}
    # hardware_info = {"Number of GPU": str(num_gpus), "Names of GPUs": gpu_name}

    # write data header
    with open(data_file_path, "a") as f:
        yaml.safe_dump(test_info, f)
        # yaml.safe_dump(hardware_info,f)

    f.close()
    ## get driver info and os info?

    return data_path, data_file_path
