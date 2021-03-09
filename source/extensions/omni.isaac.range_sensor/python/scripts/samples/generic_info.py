import omni
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from omni.isaac.range_sensor import _range_sensor
import omni.isaac.RangeSensorSchema as RangeSensorSchema
from pxr import Usd, UsdGeom, UsdLux, Sdf, Gf, UsdPhysics
import carb
import asyncio
import weakref
import numpy as np
import time

import collections

EXTENSION_NAME = "Generic Info"


class Extension(omni.ext.IExt):
    def on_startup(self):
        """
        This sample is written to demonstrate the Generic python API for Isaac Sim.
        """

        # The extension acquires the Generic Sensor interface at startup.  It will be released during extension shutdown.  We
        # create a Generic prim using our schema, and then we interact with / query that prim using the python API found
        # in generic/bindings
        self._sensor = _range_sensor.acquire_generic_sensor_interface()

        # We also need an interface to the viewport to do things like set and get camera positions
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        # self._editor = omni.kit.editor.get_editor_interface()
        self._timeline = omni.timeline.get_timeline_interface()

        ## for plotting
        # self._usd_context = omni.usd.get_context()
        # if self._usd_context is not None:
        #     self._events = self._usd_context.get_stage_event_stream()
        #     self._stage_event_sub = self._events.create_subscription_to_pop(
        #         self._on_stage_event, name="physics inspector stage event"
        #     )

        # This just defines the window we will use to access the generic_info GUI.  Note that clicking on the menu item
        # does not create an instance of generic_info; that is done by the extension when it is loaded by kit.  All this
        # menu does is show or hide our GUI we will use for interacting with generic_info
        self._window = omni.ui.Window(
            EXTENSION_NAME, width=600, height=400, visible=False, dockPreference=omni.ui.DockPreference.LEFT_BOTTOM
        )

        self._menu_items = [
            MenuItemDescription(
                name="Range Sensor",
                sub_menu=[
                    MenuItemDescription(
                        name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback()
                    )
                ],
            )
        ]
        add_menu_items(self._menu_items, "Isaac")

        self._test = False
        self.generic = False
        self._sampling_rate = 2.4e5
        self._plot = False
        self.plot_duration = 2  # in seconds
        self._record_start = time.perf_counter()

        # Kit GUIs are defined by a tree of layouts, and leaf layouts contain GUI elements (like buttons or
        # text entry fields).  You can learn more about Layouts and GUIs in the python manual at
        # Scripting API > omni.kit package > omni.ui module.
        # Each button below has a tooltip and a function that is called when the button is clicked
        with self._window.frame:
            with ui.VStack():
                ui.Label(
                    "This sample demonstrates how to create a generic range sensor, set properties and get data from it. Press play once sensor is created to simulate",
                    height=0,
                    word_wrap=True,
                )
                ui.Button(
                    "Clean Stage And Spawn a Generic Sensor",
                    clicked_fn=self._on_spawn_generic_button,
                    tooltip="Spawn an Generic Sensor in the Stage and set its properties",
                    height=0,
                )
                ui.Button(
                    "Spawn an Obstacle for the Generic Sensor",
                    clicked_fn=self._on_spawn_obstacles_button,
                    tooltip="Spawn an obstacle and move camera so its in view",
                    height=0,
                )
                ui.Button(
                    "Set Sensor Pattern",
                    clicked_fn=self._set_sensor_pattern,
                    tooltip="Press play to enable simulation and then press this button to get the current sensor information",
                    height=0,
                )
                ui.Button(
                    "Get data from the Sensor (press play first)",
                    clicked_fn=self._get_info_function,
                    tooltip="Press play to enable simulation and then press this button to get the current LIDAR information",
                    height=0,
                )
                ui.Label(
                    'Note: The buttons above only work with the sensor spawned by the "Spawn an Generic Sensor" button and not existing ones in the stage',
                    height=0,
                    word_wrap=True,
                )
                ui.Button(
                    "Plot Sensor Pattern",
                    clicked_fn=self._on_plot_sensor_pattern,
                    tooltip="Plot the sensor's hit pattern on the wall",
                    height=0,
                )
                # The separator is an example of a widget that does not contain any interactive functionality.
                # a tiny gap in the UI in order separate one part from another.
                ui.Spacer(height=5)
                ui.Separator(height=1, width=0)
                ui.Spacer(height=5)
                ui.Label("Output Information:", height=0)
                with ui.ScrollingFrame():
                    self._info_label = ui.Label("No Data To Display", word_wrap=True)

    def on_shutdown(self):
        # Perform cleanup once the sample closes
        remove_menu_items(self._menu_items, "Isaac")
        self._window = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    async def _spawn_generic_function(self, task):
        # Wait for stage clear to complete before creating Generic
        done, pending = await asyncio.wait({task})
        if task in done:
            stage = omni.usd.get_context().get_stage()

            # Set up axis to z
            UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
            UsdGeom.SetStageMetersPerUnit(stage, 0.01)

            # Create the PhysicsScene.  The generic is going to execute line trace calls in PhysX, and return a value based
            # on how far it travels before colliding with an object that is using the PhysX collision API.  Because of this,
            # to use the sensor extension, you MUST have a physics scene defined
            UsdPhysics.Scene.Define(stage, Sdf.Path("/World/physicsScene"))

            # create the Generic Sensor.  Before we can set any attributes on our sensor, we must first create the prim using our
            # Generic schema, and then populate it with the parameters we will be manipulating.  If you try to manipulate
            # a parameter before creating it, you will get a runtime error
            self.genericPath = "/World/GenericSensor"
            self.generic = RangeSensorSchema.Generic.Define(stage, Sdf.Path(self.genericPath))

            # Min and max range for the sensor.  This defines the starting and stopping locations for the linetrace
            self.generic.CreateMinRangeAttr().Set(0.4)
            self.generic.CreateMaxRangeAttr().Set(100.0)

            # sampling rate for the custom data
            self.generic.CreateSamplingRateAttr().Set(self._sampling_rate)

            # These attributes affect drawing the sensor in the viewport.
            # Draw Points = True will draw the actual rays in the viewport.
            self.generic.CreateDrawPointsAttr().Set(False)
            self.generic.CreateDrawLinesAttr().Set(False)

            # We set the attributes we created.  We could have just set the attributes at creation, but this was
            # more illustrative.  It's important to remember that attributes do not exist until you create them; even
            # if they are defined in the schema.
            self.generic.GetDrawLinesAttr().Set(True)
            # self.generic.AddTranslateOp().Set(Gf.Vec3f(0.0, 0.0, 25.0))

            # we want to make sure we can see the sensor we made, so we set the camera position and look target
            self._viewport.set_camera_position("/OmniverseKit_Persp", -500, 500, 500, True)
            self._viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)

            #
            # self._editor_event_subscription = self._editor.subscribe_to_update_events(self._on_editor_step)
            self._editor_event_subscription = (
                omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._on_editor_step)
            )

    def _on_spawn_generic_button(self):
        # wait for new stage before creating sensor
        task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._spawn_generic_function(task))

    def _on_spawn_obstacles_button(self):
        stage = omni.usd.get_context().get_stage()
        self.CubePath = "/World/Cube"
        offset = Gf.Vec3f(200.0, 0.0, 0.0)
        size = 1

        # Define a light so we can see the obstacle better
        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(500)

        # To create a cube, we first define our geometry at our chosen path.  Then, becuase
        # we will need the primitive later, we query the prim from the stage. If the prim already exists, skip creation
        if stage.GetPrimAtPath(self.CubePath):
            return
        self.cubeGeom = UsdGeom.Cube.Define(stage, self.CubePath)
        self.cubePrim = stage.GetPrimAtPath(self.CubePath)

        # Remember!  Attributes do not exist until they are created.  Here we set the value to the non defualt at
        # creation.  Note that moving the cube to a different location involves adding a translation operation to
        # our primitive.
        self.cubeGeom.CreateSizeAttr(size)
        self.cubeGeom.AddTranslateOp().Set(offset)
        UsdGeom.XformCommonAPI(self.cubePrim).SetScale((100, 500, 400))

        # In order for our cube to interact with the LIDAR, it needs to be able to colide with our physX line traces.
        # to do this, we give our cube the collision API, and set it's material and collision group.
        collisionAPI = UsdPhysics.CollisionAPI.Apply(self.cubePrim)

    def _set_sensor_pattern(self):
        self._test = True

        # custom data generation
        self._batch_size = int(1e6)
        speed_scale = 40
        sweep_range = np.pi / 4
        self.azimuth = speed_scale * sweep_range * (np.arange(self._batch_size) / self._batch_size - 0.5)
        self.zenith = np.ones(self._batch_size) * np.pi / 12
        self.sensor_pattern = np.stack((self.azimuth, self.zenith))  # first term is azimuth, second term is zenith

        # # # import data from file
        # self.sensor_pattern = np.loadtxt("filename.csv", delimiter=",")
        # self._batch_size = np.shape(self.sensor_pattern)[0]
        # self.sensor_pattern = np.deg2rad(self.sensor_pattern).T.copy()        ##  MUST USE .copy()

        # adding random offsets to the origin
        self.origin_offsets = 5 * np.random.random((self._batch_size, 3))

    def _on_editor_step(self, step):
        if not self._timeline.is_playing():
            return

        if self._timeline.is_playing():
            if self.generic and self._test:
                if self._sensor.send_next_batch(self.genericPath):
                    self._sensor.set_next_batch_rays(self.genericPath, self.sensor_pattern)
                    # add indiviaul ray offsets
                    self._sensor.set_next_batch_offsets(self.genericPath, self.origin_offsets)
            if self.generic and self._plot:
                if (time.perf_counter() - self._record_start) < self.plot_duration:
                    self.hit_pos_data = np.append(
                        self.hit_pos_data, self._sensor.get_hit_pos_data(self.genericPath), axis=0
                    )
                else:
                    self._plot = False
                    print("end plotting")
                    self.plot_pattern(self.hit_pos_data)

    def _on_plot_sensor_pattern(self):
        if not self._timeline.is_playing():
            print("press play first")
            return

        self.hit_pos_data = np.empty((0, 3))
        self._plot = True
        print("start plotting")
        self._record_start = time.perf_counter()

    def plot_pattern(self, data):
        import PIL.ImageDraw as ImageDraw, PIL.Image as Image, PIL.ImageShow as ImageShow

        ## set up plot window
        window_length = 600
        window_height = 400
        origin = [window_length / 2.0, window_height / 2.0]

        hit_yz = self.data_processing(data)

        # scale data with the wall size
        cube_size = self.cubePrim.GetAttribute("xformOp:scale").Get()
        height_ratio = window_height / float(cube_size[2])
        length_ratio = window_length / float(cube_size[1])
        plot_scale = min(height_ratio, length_ratio)

        # scale, axis_align, and center data to plot on PIL coordinate
        hit_yz = plot_scale * hit_yz
        plot_x = origin[0] - hit_yz[:, 0]
        plot_y = origin[1] - hit_yz[:, 1]

        plot_data = np.stack([plot_x, plot_y], axis=1)
        xy = plot_data.ravel()

        ## actual plotting
        im = Image.new("RGB", (window_length, window_height))
        draw = ImageDraw.Draw(im)
        draw.point(xy.tolist(), fill=255)

        im.show()

    def data_processing(self, data):
        ## only plotting when the wall is offsetted x as in the example no rotation or other axial offsets.
        # find where is the surface of the wall
        cube_pos = self.cubePrim.GetAttribute("xformOp:translate").Get()
        cube_size = self.cubePrim.GetAttribute("xformOp:scale").Get()
        wall_loc = cube_pos[0] - np.sign(cube_pos[0]) * cube_size[0] / 2

        ## find in data the group that has the right offset
        hit_idx = np.where(np.isclose(data[:, 0], wall_loc, rtol=1e2))
        if len(hit_idx) == 0:
            print("no ray hit the wall")
            return np.array([])
        else:
            hit_pts = np.squeeze(data[hit_idx, 1:3])
            return hit_pts

    def _get_info_function(self):
        depth = self._sensor.get_depth_data(self.genericPath)
        linear_depth = self._sensor.get_linear_depth_data(self.genericPath)
        intensity = self._sensor.get_intensity_data(self.genericPath)

        zenith = self._sensor.get_zenith_data(self.genericPath)
        azimuth = self._sensor.get_azimuth_data(self.genericPath)

        ## convert depth?
        print("depth", depth)
        print("zenith", zenith)
        print("azimuth", azimuth)
        print("linear depth", linear_depth)
        print("intensity", intensity)
