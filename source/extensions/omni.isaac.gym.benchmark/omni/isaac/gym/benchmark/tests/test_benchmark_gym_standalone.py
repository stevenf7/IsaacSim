# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import subprocess

import carb
import omni.kit
import omni.kit.test
import omni.timeline
from omni.isaac.benchmark.services.base_isaac_benchmark import BaseIsaacBenchmark

MAX_ITERATIONS = 10

# get path to python .sh/bat using app folder path
PYTHON_EXE = (
    os.path.abspath(os.path.join(carb.tokens.get_tokens_interface().resolve("${app}") + "/../"))
    + "/python"
    + carb.tokens.get_tokens_interface().resolve("${shell_ext}")
)

REPO_PATH = os.path.abspath(
    os.path.join(carb.tokens.get_tokens_interface().resolve("${app}") + "/../tests/OmniIsaacGymEnvs/")
)


def _get_camera_app_file():
    src_app_file = f"{REPO_PATH}/apps/omni.isaac.sim.python.gym.camera.kit"
    dst_app_file = os.path.join(
        carb.tokens.get_tokens_interface().resolve("${app}"), "omni.isaac.sim.python.gym.camera.kit"
    )
    if not os.path.exists(dst_app_file):
        os.symlink(src_app_file, dst_app_file)

    def update_app_file():
        file = open(dst_app_file, "r")
        lines = file.readlines()[:-1]
        lines.append('folders = ["${app}/../exts", "${app}/../extscache", "${app}/../extsPhysics"]')
        file.close()
        file = open(dst_app_file, "w")
        file.writelines(lines)

    update_app_file()
    return dst_app_file


def _run_rlgames_train(script, task, pipeline, sim_device, headless, max_iterations=0, dr=False, warp=False):
    os.chdir(os.path.join(REPO_PATH, "omniisaacgymenvs"))
    cmd = [
        PYTHON_EXE,
        f"scripts/{script}.py",
        f"headless={headless}",
        f"task={task}",
        f"sim_device={sim_device}",
        f"pipeline={pipeline}",
        "seed=42",
    ]
    if dr:
        cmd.append("task.domain_randomization.randomize=True")
    if warp:
        cmd.append("warp=True")
    if max_iterations > 0:
        cmd.append(f"max_iterations={max_iterations}")
    if task == "AntSAC":
        cmd.append("train=AntSAC")
    elif task == "HumanoidSAC":
        cmd.append("train=HumanoidSAC")

    if task == "CartpoleCamera":
        app_file = _get_camera_app_file()
        cmd.append(f"kit_app={app_file}")

    experiment_name = f"{task}_{sim_device}_{pipeline}"

    if dr:
        experiment_name += "_dr"
    cmd.append(f"experiment={experiment_name}")

    subprocess.check_call(cmd)

    return experiment_name


class TestBenchmarkGymStandalone(BaseIsaacBenchmark):
    def __init__(self, *args, **kwargs):
        super(TestBenchmarkGymStandalone, self).__init__(*args, **kwargs)

    async def setUp(self):
        await super().setUp()
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    async def benchmark_train(self, task, headless, dr=False, warp=False):
        self.set_phase("train_benchmark")
        self.start_runtime()
        _run_rlgames_train("rlgames_train", task, self._pipeline, self._sim_device, headless, MAX_ITERATIONS, dr, warp)
        self.stop_runtime()
        await self.store_measurements()

    # ----------------------------------------------------------------------
    async def test_allegro_hand_standalone_render(self):
        task = "AllegroHand"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_render"
        await self.benchmark_train(task=task, headless=False)

    async def test_allegro_hand_standalone_headless(self):
        task = "AllegroHand"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_headless"
        await self.benchmark_train(task=task, headless=True)

    async def test_ant_standalone_render(self):
        task = "Ant"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_render"
        await self.benchmark_train(task=task, headless=False)

    async def test_ant_standalone_headless(self):
        task = "Ant"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_headless"
        await self.benchmark_train(task=task, headless=True)

    async def test_anymal_terrain_standalone_render(self):
        task = "AnymalTerrain"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_render"
        await self.benchmark_train(task=task, headless=False)

    async def test_anymal_terrain_standalone_headless(self):
        task = "AnymalTerrain"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_headless"
        await self.benchmark_train(task=task, headless=True)

    async def test_cartpole_standalone_render(self):
        task = "Cartpole"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_render"
        await self.benchmark_train(task=task, headless=False)

    async def test_cartpole_standalone_headless(self):
        task = "Cartpole"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_headless"
        await self.benchmark_train(task=task, headless=True)

    async def test_cartpole_camera_standalone_render(self):
        task = "CartpoleCamera"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_render"
        await self.benchmark_train(task=task, headless=False)

    async def test_cartpole_camera_standalone_headless(self):
        task = "CartpoleCamera"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_headless"
        await self.benchmark_train(task=task, headless=True)

    async def test_franka_cabinet_standalone_render(self):
        task = "FrankaCabinet"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_render"
        await self.benchmark_train(task=task, headless=False)

    async def test_franka_cabinet_standalone_headless(self):
        task = "FrankaCabinet"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_headless"
        await self.benchmark_train(task=task, headless=True)

    async def test_franka_deformable_standalone_render(self):
        task = "FrankaDeformable"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_render"
        await self.benchmark_train(task=task, headless=False)

    async def test_franka_deformable_standalone_headless(self):
        task = "FrankaDeformable"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_headless"
        await self.benchmark_train(task=task, headless=True)

    async def test_humanoid_standalone_render(self):
        task = "Humanoid"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_render"
        await self.benchmark_train(task=task, headless=False)

    async def test_humanoid_standalone_headless(self):
        task = "Humanoid"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_headless"
        await self.benchmark_train(task=task, headless=True)

    async def test_ingenuity_standalone_render(self):
        task = "Ingenuity"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_render"
        await self.benchmark_train(task=task, headless=False)

    async def test_ingenuity_standalone_headless(self):
        task = "Ingenuity"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_headless"
        await self.benchmark_train(task=task, headless=True)

    async def test_shadow_hand_standalone_render(self):
        task = "ShadowHand"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_render"
        await self.benchmark_train(task=task, headless=False)

    async def test_shadow_hand_standalone_headless(self):
        task = "ShadowHand"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_headless"
        await self.benchmark_train(task=task, headless=True)

    async def test_shadow_hand_openai_lstm_standalone_render(self):
        task = "ShadowHandOpenAI_LSTM"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_render"
        await self.benchmark_train(task=task, headless=False)

    async def test_shadow_hand_openai_lstm_standalone_headless(self):
        task = "ShadowHandOpenAI_LSTM"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_headless"
        await self.benchmark_train(task=task, headless=True)

    async def test_shadow_hand_openai_ff_standalone_render(self):
        task = "ShadowHandOpenAI_FF"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_render"
        await self.benchmark_train(task=task, headless=False)

    async def test_shadow_hand_openai_ff_standalone_headless(self):
        task = "ShadowHandOpenAI_FF"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_headless"
        await self.benchmark_train(task=task, headless=True)

    async def test_cartpole_warp_standalone_render(self):
        task = "Cartpole"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_warp_standalone_render"
        await self.benchmark_train(task=task, headless=False, warp=True)

    async def test_cartpole_warp_standalone_headless(self):
        task = "Cartpole"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_warp_standalone_headless"
        await self.benchmark_train(task=task, headless=True, warp=True)

    async def test_ant_warp_standalone_render(self):
        task = "Ant"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_warp_standalone_render"
        await self.benchmark_train(task=task, headless=False, warp=True)

    async def test_ant_warp_standalone_headless(self):
        task = "Ant"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_warp_standalone_headless"
        await self.benchmark_train(task=task, headless=True, warp=True)

    async def test_humanoid_warp_standalone_render(self):
        task = "Humanoid"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_warp_standalone_render"
        await self.benchmark_train(task=task, headless=False, warp=True)

    async def test_humanoid_warp_standalone_headless(self):
        task = "Humanoid"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_warp_standalone_headless"
        await self.benchmark_train(task=task, headless=True, warp=True)


class TestBenchmarkGymStandaloneGG(TestBenchmarkGymStandalone):
    def __init__(self, *args, **kwargs):
        TestBenchmarkGymStandalone.__init__(self, *args, **kwargs)
        self._pipeline = "gpu"
        self._sim_device = "gpu"

    async def test_factory_pick_standalone_render(self):
        task = "FactoryTaskNutBoltPick"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_render"
        await self.benchmark_train(task=task, headless=False)

    async def test_factory_pick_standalone_headless(self):
        task = "FactoryTaskNutBoltPick"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_headless"
        await self.benchmark_train(task=task, headless=True)

    async def test_factory_place_standalone_render(self):
        task = "FactoryTaskNutBoltPlace"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_render"
        await self.benchmark_train(task=task, headless=False)

    async def test_factory_place_standalone_headless(self):
        task = "FactoryTaskNutBoltPlace"
        await self.benchmark_train(task=task, headless=True)

    async def test_factory_standalone_screw_render(self):
        task = "FactoryTaskNutBoltScrew"
        self.test_run.test_name = f"{task}_{self._pipeline}_{self._sim_device}_standalone_render"
        await self.benchmark_train(task=task, headless=False)

    async def test_factory_screw_standalone_headless(self):
        task = "FactoryTaskNutBoltScrew"
        await self.benchmark_train(task=task, headless=True)


class TestBenchmarkGymStandaloneGC(TestBenchmarkGymStandalone):
    def __init__(self, *args, **kwargs):
        TestBenchmarkGymStandalone.__init__(self, *args, **kwargs)
        self._pipeline = "cpu"
        self._sim_device = "gpu"


class TestBenchmarkGymStandaloneCC(TestBenchmarkGymStandalone):
    def __init__(self, *args, **kwargs):
        TestBenchmarkGymStandalone.__init__(self, *args, **kwargs)
        self._pipeline = "cpu"
        self._sim_device = "cpu"
