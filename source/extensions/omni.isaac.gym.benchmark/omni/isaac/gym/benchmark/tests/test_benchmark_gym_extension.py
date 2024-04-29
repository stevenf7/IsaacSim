# Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit
import omni.kit.test
import omni.timeline
from omni.isaac.benchmark.services import BaseIsaacBenchmarkAsync
from omniisaacgymenvs import RLExtension, get_instance

MAX_ITERATIONS = 10


class TestBenchmarkGymExtension(BaseIsaacBenchmarkAsync):
    def __init__(self, *args, **kwargs):
        super(TestBenchmarkGymExtension, self).__init__(*args, **kwargs)
        self._ext = get_instance()

    async def setUp(self):
        await super().setUp()
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    async def benchmark_load_scene(self, task, render_mode):
        # apply render mode
        self._ext._render_dropdown.get_item_value_model().set_value(render_mode)

        task_idx = self._ext._task_list.index(task)
        self._ext._task_dropdown.get_item_value_model().set_value(task_idx)

        if not omni.usd.get_context().get_stage().GetPrimAtPath("/World/envs").IsValid():
            self._ext._parse_config(task=task, num_envs=self._ext._num_envs_int.get_value_as_int())
            self._ext.create_task()

        self._ext._env._world._sim_params = self._ext._sim_config.get_physics_params()
        await self._ext._env._world.initialize_simulation_context_async()

        # clear scene
        self._ext._env._world.scene.clear()
        # clear environments added to world
        omni.usd.get_context().get_stage().RemovePrim("/World/collisions")
        omni.usd.get_context().get_stage().RemovePrim("/World/envs")

        # create scene
        self.set_phase("scene_loading")
        await self._ext._env._world.reset_async_set_up_scene()
        await self.store_measurements()

    async def benchmark_train(self, task, max_iterations=None):
        overrides = None
        if max_iterations is not None:
            if overrides is None:
                overrides = [f"max_iterations={max_iterations}"]
            else:
                overrides += [f"max_iterations={max_iterations}"]

        self.set_phase("train_benchmark")
        await self._ext._on_train_async(overrides=overrides)
        await self.store_measurements()

        omni.timeline.get_timeline_interface().stop()

    async def benchmark_step(self, task, render_mode, step_num=20):
        # apply render mode
        self._ext._render_dropdown.get_item_value_model().set_value(render_mode)

        # benchmark simulation startup time
        self.set_phase("sim_start")
        omni.timeline.get_timeline_interface().play()
        await omni.kit.app.get_app().next_update_async()
        await self.store_measurements()

        # benchmark step time (simulation only)
        self.set_phase("sim_benchmark")
        for _ in range(step_num):
            await omni.kit.app.get_app().next_update_async()
        await self.store_measurements()

        omni.timeline.get_timeline_interface().stop()

    # ----------------------------------------------------------------------
    async def test_allegro_hand_extension_render(self):
        task = "AllegroHand"
        self.test_run.test_name = f"{task}_extension_render"
        await self.benchmark_load_scene(task=task, render_mode=0)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=0)

    async def test_allegro_hand_extension_no_render(self):
        task = "AllegroHand"
        self.test_run.test_name = f"{task}_extension_no_render"
        await self.benchmark_load_scene(task=task, render_mode=2)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=2)

    async def test_ant_extension_render(self):
        task = "Ant"
        self.test_run.test_name = f"{task}_extension_render"
        await self.benchmark_load_scene(task=task, render_mode=0)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=0)

    async def test_ant_extension_no_render(self):
        task = "Ant"
        self.test_run.test_name = f"{task}_extension_no_render"
        await self.benchmark_load_scene(task=task, render_mode=2)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=2)

    async def test_anymal_terrain_extension_render(self):
        task = "AnymalTerrain"
        self.test_run.test_name = f"{task}_extension_render"
        await self.benchmark_load_scene(task=task, render_mode=0)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=0)

    async def test_anymal_terrain_extension_no_render(self):
        task = "AnymalTerrain"
        self.test_run.test_name = f"{task}_extension_no_render"
        await self.benchmark_load_scene(task=task, render_mode=2)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=2)

    async def test_cartpole_extension_render(self):
        task = "Cartpole"
        self.test_run.test_name = f"{task}_extension_render"
        await self.benchmark_load_scene(task=task, render_mode=0)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=0)

    async def test_cartpole_extension_no_render(self):
        task = "Cartpole"
        self.test_run.test_name = f"{task}_extension_no_render"
        await self.benchmark_load_scene(task=task, render_mode=2)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=2)

    async def test_factory_pick_extension_render(self):
        task = "FactoryTaskNutBoltPick"
        self.test_run.test_name = f"{task}_extension_render"
        await self.benchmark_load_scene(task=task, render_mode=0)
        for _ in range(10000):
            await omni.kit.app.get_app().next_update_async()
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=0)

    async def test_factory_pick_extension_no_render(self):
        task = "FactoryTaskNutBoltPick"
        self.test_run.test_name = f"{task}_extension_no_render"
        await self.benchmark_load_scene(task=task, render_mode=2)
        for _ in range(10000):
            await omni.kit.app.get_app().next_update_async()
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=2)

    async def test_factory_place_extension_render(self):
        task = "FactoryTaskNutBoltPlace"
        self.test_run.test_name = f"{task}_extension_render"
        await self.benchmark_load_scene(task=task, render_mode=0)
        for _ in range(10000):
            await omni.kit.app.get_app().next_update_async()
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=0)

    async def test_factory_place_extension_no_render(self):
        task = "FactoryTaskNutBoltPlace"
        self.test_run.test_name = f"{task}_extension_no_render"
        await self.benchmark_load_scene(task=task, render_mode=2)
        for _ in range(10000):
            await omni.kit.app.get_app().next_update_async()
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=2)

    async def test_factory_extension_screw_render(self):
        task = "FactoryTaskNutBoltScrew"
        self.test_run.test_name = f"{task}_extension_render"
        await self.benchmark_load_scene(task=task, render_mode=0)
        for _ in range(10000):
            await omni.kit.app.get_app().next_update_async()
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=0)

    async def test_factory_screw_extension_no_render(self):
        task = "FactoryTaskNutBoltScrew"
        self.test_run.test_name = f"{task}_extension_no_render"
        await self.benchmark_load_scene(task=task, render_mode=2)
        for _ in range(10000):
            await omni.kit.app.get_app().next_update_async()
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=2)

    async def test_franka_cabinet_extension_render(self):
        task = "FrankaCabinet"
        self.test_run.test_name = f"{task}_extension_render"
        await self.benchmark_load_scene(task=task, render_mode=0)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=0)

    async def test_franka_cabinet_extension_no_render(self):
        task = "FrankaCabinet"
        self.test_run.test_name = f"{task}_extension_no_render"
        await self.benchmark_load_scene(task=task, render_mode=2)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=2)

    async def test_franka_deformable_extension_render(self):
        task = "FrankaDeformable"
        self.test_run.test_name = f"{task}_extension_render"
        await self.benchmark_load_scene(task=task, render_mode=0)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=0)

    async def test_franka_deformable_extension_no_render(self):
        task = "FrankaDeformable"
        self.test_run.test_name = f"{task}_extension_no_render"
        await self.benchmark_load_scene(task=task, render_mode=2)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=2)

    async def test_humanoid_extension_render(self):
        task = "Humanoid"
        self.test_run.test_name = f"{task}_extension_render"
        await self.benchmark_load_scene(task=task, render_mode=0)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=0)

    async def test_humanoid_extension_no_render(self):
        task = "Humanoid"
        self.test_run.test_name = f"{task}_extension_no_render"
        await self.benchmark_load_scene(task=task, render_mode=2)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=2)

    async def test_ingenuity_extension_render(self):
        task = "Ingenuity"
        self.test_run.test_name = f"{task}_extension_render"
        await self.benchmark_load_scene(task=task, render_mode=0)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=0)

    async def test_ingenuity_extension_no_render(self):
        task = "Ingenuity"
        self.test_run.test_name = f"{task}_extension_no_render"
        await self.benchmark_load_scene(task=task, render_mode=2)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=2)

    async def test_shadow_hand_extension_render(self):
        task = "ShadowHand"
        self.test_run.test_name = f"{task}_extension_render"
        await self.benchmark_load_scene(task=task, render_mode=0)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=0)

    async def test_shadow_hand_extension_no_render(self):
        task = "ShadowHand"
        self.test_run.test_name = f"{task}_extension_no_render"
        await self.benchmark_load_scene(task=task, render_mode=2)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=2)

    async def test_shadow_hand_openai_lstm_extension_render(self):
        task = "ShadowHandOpenAI_LSTM"
        self.test_run.test_name = f"{task}_extension_render"
        await self.benchmark_load_scene(task=task, render_mode=0)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=0)

    async def test_shadow_hand_openai_lstm_extension_no_render(self):
        task = "ShadowHandOpenAI_LSTM"
        self.test_run.test_name = f"{task}_extension_no_render"
        await self.benchmark_load_scene(task=task, render_mode=2)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=2)

    async def test_shadow_hand_openai_ff_extension_render(self):
        task = "ShadowHandOpenAI_FF"
        self.test_run.test_name = f"{task}_extension_render"
        await self.benchmark_load_scene(task=task, render_mode=0)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=0)

    async def test_shadow_hand_openai_ff_extension_no_render(self):
        task = "ShadowHandOpenAI_FF"
        self.test_run.test_name = f"{task}_extension_no_render"
        await self.benchmark_load_scene(task=task, render_mode=2)
        await self.benchmark_train(task=task, max_iterations=MAX_ITERATIONS)
        await self.benchmark_step(task=task, render_mode=2)
