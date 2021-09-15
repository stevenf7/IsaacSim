import omni.ext
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

import gc
import asyncio
import weakref
import omni.physx as _physx
from .robot_benchmarking import RobotBenchmark
from omni.isaac.benchmark_environments.scripts.environments import EnvironmentCreator
from .benchmark_utils import BenchmarkConfigUtility


EXTENSION_NAME = "Robot Benchmark"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self._window = ui.Window(EXTENSION_NAME, width=800, height=400, visible=False)
        self._window.set_visibility_changed_fn(self._on_window)
        self._menu_items = [
            MenuItemDescription(name="Default Benchmarks", onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]

        add_menu_items(self._menu_items, "Robot Benchmark")
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._timeline = omni.timeline.get_timeline_interface()

        self._benchmarking = RobotBenchmark()
        # Simple button style that grays out the button if disabled
        self._button_style = {":disabled": {"color": 0xFF000000}}

        self._selected_environment = None

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self.mg_ext_id = ext_manager.get_enabled_extension_id("omni.isaac.motion_generation")
        mg_extension_path = ext_manager.get_extension_path(self.mg_ext_id)

        self.ext_id = ext_id
        benchmark_extension_path = ext_manager.get_extension_path(self.ext_id)

        self.benchmark_config_util = BenchmarkConfigUtility(mg_extension_path, benchmark_extension_path)

        self.env_creator = EnvironmentCreator()
        self.get_robot_options()

        with self._window.frame:
            with omni.ui.VStack(style=self._button_style):
                with ui.HStack(height=30):
                    ui.Label("Selected Environment", width=0)
                    ui.Spacer(width=5)
                    self._selected_environment = ui.ComboBox(0, *self.env_creator.get_environment_names())
                    s = self._selected_environment.model.get_item_value_model().subscribe_value_changed_fn(
                        self.on_env_selection
                    )
                    self.env_selection_subscription = s

                with ui.HStack(height=30):
                    ui.Label("Selected Robot", width=0)
                    ui.Spacer(width=5)
                    self._robot_frame = ui.Frame()
                    with self._robot_frame:
                        self._selected_robot = ui.ComboBox(0, *self.robot_options)
                        s = self._selected_robot.model.get_item_value_model().subscribe_value_changed_fn(
                            self.on_robot_selection
                        )
                        self.robot_selection_subscription = s

                with ui.HStack(height=30):
                    ui.Label("Selected Motion Policy", width=0)
                    ui.Spacer(width=5)
                    self._policy_frame = ui.Frame()
                    self.get_motion_policy_options()
                    with self._policy_frame:
                        self._selected_policy = ui.ComboBox(0, *self.policy_options)

                self._create_robot_btn = ui.Button("Load Robot", enabled=True)
                self._create_robot_btn.set_clicked_fn(self._on_setup_environment)
                self._create_robot_btn.set_tooltip("Load robot and environment")

                self._test_btn = ui.Button("Start Test", enabled=False)
                self._test_btn.set_clicked_fn(self._benchmarking.toggle_testing)
                self._test_btn.set_tooltip("Begin Test")

                self._target_following_btn = ui.Button("Play Around", enabled=False)
                self._target_following_btn.set_clicked_fn(self._benchmarking.follow_target)
                self._target_following_btn.set_tooltip("Create a target you can move around with your mouse")

                self._reset_btn = ui.Button("Reset", enabled=False)
                self._reset_btn.set_clicked_fn(self._benchmarking.reset)
                self._reset_btn.set_tooltip("Reset Robot to default position")

    def on_env_selection(self, option):
        """
        callback any time a new environment is selected from the drop-down menu:
            Reload the list of possible robots and motion policies in the selected environment.
        """
        with self._robot_frame:
            self.get_robot_options()
            self._selected_robot = ui.ComboBox(0, *self.robot_options)
            s = self._selected_robot.model.get_item_value_model().subscribe_value_changed_fn(self.on_robot_selection)
            self.robot_selection_subscription = s

        with self._policy_frame:
            self.get_motion_policy_options()
            self._selected_policy = ui.ComboBox(0, *self.policy_options)

    def on_robot_selection(self, option):
        """
        callback any time a new robot is selected in the drop-down menu:
            Reload the list of possible motion policies for the selected robot.
        """
        with self._policy_frame:
            self.get_motion_policy_options()
            self._selected_policy = ui.ComboBox(0, *self.policy_options)

    def get_robot_options(self):
        """
        Given the environment selected in the drop-down menu, return a list of the robots that have at least one
        motion policy configured in the motion_generation extension, and are not explicitly excluded for this
        environment
        """

        if self._selected_environment is None:
            env_name = self.env_creator.get_environment_names()[0]
        else:
            selected_environment = self._selected_environment.model.get_item_value_model().as_int
            env_name = self.env_creator.get_environment_names()[selected_environment]

        robot_exclusion_list = self.env_creator.get_robot_exclusion_list(env_name)

        self.robot_options = self.benchmark_config_util.get_robot_options(robot_exclusion_list)

    def get_motion_policy_options(self):
        """
        Given the robot selected in the drop down menu, return the motion policies that have default configs
        for the robot in the motion_generation extension
        """
        selected_robot = self.robot_options[self._selected_robot.model.get_item_value_model().as_int]

        if self._selected_environment is None:
            env_name = self.env_creator.get_environment_names()[0]
        else:
            selected_environment_idx = self._selected_environment.model.get_item_value_model().as_int
            env_name = self.env_creator.get_environment_names()[selected_environment_idx]

        policy_exclusion_list = self.env_creator.get_motion_policy_exclusion_list(env_name)
        self.policy_options = self.benchmark_config_util.get_motion_policy_options(
            selected_robot, policy_exclusion_list
        )

    def _on_window(self, status):
        if status:
            self._sub_stage_event = (
                omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(self._on_stage_event)
            )
            self._physx_subs = _physx.get_physx_interface().subscribe_physics_step_events(self._on_simulation_step)
            self._timeline_sub = self._timeline.get_timeline_event_stream().create_subscription_to_pop(
                self._on_timeline_event
            )
        else:
            self._sub_stage_event = None
            self._physx_subs = None
            self._timeline_sub = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def _on_stage_event(self, event):
        """This function is called when stage events occur.
        Enables UI elements when stage is opened.
        Prevents tasks from being started until all assets are loaded

        Arguments:
            event (int): event type
        """
        if event.type == int(omni.usd.StageEventType.OPENED):
            self._create_robot_btn.enabled = True
            self._target_following_btn.enabled = False
            self._test_btn.enabled = False

            self._reset_btn.enabled = False

            self._timeline.stop()
            self._benchmarking.stop_tasks()

    def _on_simulation_step(self, step):
        if self._benchmarking.created:
            self._create_robot_btn.text = "Reload Robot"
            if self._timeline.is_playing():
                self._benchmarking.step(step)
                self._target_following_btn.text = "Play Around"

            else:
                self._target_following_btn.text = "Press Play To Enable"
                self._test_btn.text = "Press Play To Enable"

        else:
            self._create_robot_btn.text = "Load Robot"
            self._target_following_btn.text = "Press Load Robot To Enable"
            self._test_btn.text = "Press Load Robot To Enable"

    def _on_timeline_event(self, e):
        if e.type == int(omni.timeline.TimelineEventType.PLAY):
            self._target_following_btn.enabled = True
            self._test_btn.enabled = True
            self._reset_btn.enabled = True

        if e.type == int(omni.timeline.TimelineEventType.STOP) or e.type == int(omni.timeline.TimelineEventType.PAUSE):
            self._target_following_btn.enabled = False
            self._test_btn.enabled = False

    def _on_setup_environment(self):
        self._timeline.stop()
        task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._on_create_robot(task))

    async def _on_create_robot(self, task):
        done, pending = await asyncio.wait({task})
        if task not in done:
            return

        selected_environment = self._selected_environment.model.get_item_value_model().as_int
        env_name = self.env_creator.get_environment_names()[selected_environment]

        robot_name = self.robot_options[self._selected_robot.model.get_item_value_model().as_int]
        policy_name = self.policy_options[self._selected_policy.model.get_item_value_model().as_int]

        robot_assets = self.benchmark_config_util.get_robot_assets(robot_name)

        env_kwargs = self.benchmark_config_util.get_environment_params(env_name, robot_name)
        env = self.env_creator.create_environment(env_name, **env_kwargs)

        default_policy_config = self.benchmark_config_util.get_default_policy_config(robot_name, policy_name)
        final_policy_config = self.benchmark_config_util.overwrite_default_policy_config(
            env_name, robot_name, policy_name, default_policy_config
        )

        self._benchmarking.initialize_test(env, robot_assets, final_policy_config)

        self._viewport.set_camera_position("/OmniverseKit_Persp", *env.camera_position, True)
        self._viewport.set_camera_target("/OmniverseKit_Persp", *env.camera_target, True)

        self._reset_btn.enabled = True

    def on_shutdown(self):
        self._physx_subs = None
        self._sub_stage_event = None
        self._timeline_sub = None

        self._timeline.stop()
        self._benchmarking.stop_tasks()
        self._benchmarking = None
        remove_menu_items(self._menu_items, "Robot Benchmark")
        gc.collect()
        pass
