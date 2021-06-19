# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from omni.isaac.range_sensor import _range_sensor
from pxr import UsdGeom, UsdLux, Sdf, Gf, UsdPhysics
from omni.physx.scripts.physicsUtils import *
import asyncio
import weakref

EXTENSION_NAME = "Ultrasonic Info"


class Extension(omni.ext.IExt):
    def on_startup(self):
        """
        This sample is written to demonstrate the ULTRASONIC python API for Isaac Sim.
        """

        # The extension acquires the ULTRASONIC interface at startup.  It will be released during extension shutdown.  We
        # create a ULTRASONIC prim using our schema, and then we interact with / query that prim using the python API found
        # in ultrasonic/bindings
        self._ul = _range_sensor.acquire_ultrasonic_sensor_interface()

        # We also need an interface to the viewport to do things like set and get camera positions
        self._viewport = omni.kit.viewport.get_default_viewport_window()

        # This just defines the window we will use to access the ultrasonic_info GUI.  Note that clicking on the menu item
        # does not create an instance of ultrasonic_info; that is done by the extension when it is loaded by kit.  All this
        # menu does is show or hide our GUI we will use for interacting with ultrasonic_info
        self._window = omni.ui.Window(
            EXTENSION_NAME, width=600, height=400, visible=False, dockPreference=omni.ui.DockPreference.LEFT_BOTTOM
        )

        self._menu_items = [
            MenuItemDescription(
                name="Sensing",
                sub_menu=[
                    MenuItemDescription(name="Ultrasonic", onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
                ],
            )
        ]
        add_menu_items(self._menu_items, "Isaac Examples")

        # Kit GUIs are defined by a tree of layouts, and leaf layouts contain GUI elements (like buttons or
        # text entry fields).  You can learn more about Layouts and GUIs in the python manual at
        # Scripting API > omni.kit package > omni.ui module.
        # Each button below has a tooltip and a function that is called when the button is clicked
        with self._window.frame:
            with ui.HStack():
                with ui.VStack(width=ui.Percent(50)):
                    ui.Label(
                        "This sample demonstrates how to create an ultrasonic sensor, set properties and get data from it. Press play once the sensor is created to simulate",
                        height=0,
                        word_wrap=True,
                    )
                    ui.Button(
                        "Clean Stage And Spawn an Ultrasonic Sensor",
                        clicked_fn=self._on_spawn_ultrasonic_button,
                        tooltip="Spawn an Ultrasonic Sensor in the Stage and set its properties",
                        height=0,
                    )
                    ui.Button(
                        "Spawn an Obstacle for the Ultrasonic Sensor",
                        clicked_fn=self._on_spawn_obstacles_button,
                        tooltip="Spawn an obstacle and move camera so its in view",
                        height=0,
                    )
                    ui.Button(
                        "Get data from the Ultrasonic Sensor (press play first)",
                        clicked_fn=self._get_info_function,
                        tooltip="Press play to enable simulation and then press this button to get the current ultrasonic information",
                        height=0,
                    )
                    ui.Label(
                        'Note: The buttons above only work with the ultrasonic spawned by the "Spawn an Ultrasonic Sensor" button and not existing ones in the stage',
                        height=0,
                        word_wrap=True,
                    )
                    # The separator is an example of a widget that does not contain any interactive functionality.
                    # a tiny gap in the UI in order separate one part from another.
                    ui.Spacer(height=5)
                    ui.Separator(height=1, width=0)
                    ui.Spacer(height=5)
                    ui.Label("Output Information:", height=0)
                    with ui.ScrollingFrame():
                        self._info_label = ui.Label("No Data To Display", word_wrap=True)
                ui.Spacer(width=20)
                with ui.Frame():
                    self._envelope_frame = ui.ScrollingFrame()

        # # we add a scrolling frame because we also want to display information about our ULTRASONIC, and the amount
        # # of information we display depends on the ULTRASONIC parameters.
        # scrolling_frame = sublayout.add_child(omni.kit.ui.ScrollingFrame("", -1, -1))
        # self.info_label = scrolling_frame.add_child(
        #     omni.kit.ui.Label("", useclipboard=True, clippingmode=omni.kit.ui.ClippingType.WRAP)
        # )

    def on_shutdown(self):
        # Perform cleanup once the sample closes
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    async def _spawn_ultrasonic_function(self, task):
        # Wait for stage clear to complete before creating ULTRASONIC
        done, pending = await asyncio.wait({task})
        if task in done:
            stage = omni.usd.get_context().get_stage()

            # Set up axis to z.  The ULTRASONIC extension scans in the XZ plane, which is assumed to be perpendicular to the
            # rotational plane, and so to use the ULTRASONIC as it is currently written, Z must be up.
            UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
            UsdGeom.SetStageMetersPerUnit(stage, 0.01)

            # Create the PhysicsScene.  The ultrasonic is going to execute line trace calls in PhysX, and return a value based
            # on how far it travels before colliding with an object that is using the PhysX collision API.  Because of this,
            # to use the ULTRASONIC extension, you MUST have a physics scene defined
            UsdPhysics.Scene.Define(stage, Sdf.Path("/World/physicsScene"))

            # List of poses that define the emitter prims
            origin = Gf.Vec3d(4.8, 6.4, 0.0)

            emitter_poses = [
                ((0, 0, 75.0), Gf.Vec3d(3.844, 0.9384, 0.525)),
                ((0, 0, 30.0), Gf.Vec3d(4.046, 0.7735, 0.56)),
                ((0, 0, 11.8), Gf.Vec3d(4.172, 0.3256, 0.591)),
                ((0, 0, -11.8), Gf.Vec3d(4.172, -0.3256, 0.591)),
                ((0, 0, -30.0), Gf.Vec3d(4.046, -0.7735, 0.561)),
                ((0, 0, -75.0), Gf.Vec3d(3.844, -0.9384, 0.525)),
                ((0, 0, 99.2), Gf.Vec3d(-1.454, 0.9352, 0.5367)),
                ((0, 0, 150.0), Gf.Vec3d(-1.789, 0.788, 0.558)),
                ((0, 0, 175.5), Gf.Vec3d(-1.887, 0.36, 0.6249)),
                ((0, 0, -175.5), Gf.Vec3d(-1.887, -0.36, 0.6249)),
                ((0, 0, -150.0), Gf.Vec3d(-1.789, -0.788, 0.558)),
                ((0, 0, -99.2), Gf.Vec3d(-1.454, -0.9352, 0.5367)),
            ]

            adjacency = [
                [0, 1],
                [0, 1, 2],
                [1, 2, 3],
                [2, 3, 4],
                [3, 4, 5],
                [4, 5],
                [6, 7],
                [6, 7, 8],
                [7, 8, 9],
                [8, 9, 10],
                [9, 10, 11],
                [10, 11],
            ]
            emitters = []
            for i in range(len(emitter_poses)):
                pose = emitter_poses[i]
                adjacent = adjacency[i]
                result, emitter_prim = omni.kit.commands.execute(
                    "RangeSensorCreateUltrasonicEmitter",
                    path="/World/UltrasonicEmitter",
                    per_ray_intensity=0.4,
                    yaw_offset=0.0,
                    adjacency_list=adjacent,
                )
                emitter_prim.GetPrim().GetAttribute("xformOp:translate").Set((origin + pose[1]) / 0.01)
                emitter_prim.GetPrim().GetAttribute("xformOp:rotateXYZ").Set(pose[0])
                emitters.append(emitter_prim)
            emitter_paths = [emitter.GetPath() for emitter in emitters]

            result, group_1 = omni.kit.commands.execute(
                "RangeSensorCreateUltrasonicFiringGroup",
                path="/World/UltrasonicFiringGroup_0",
                emitter_modes=[(0, 1), (3, 0), (4, 1), (7, 0), (8, 1), (11, 0)],
                receiver_modes=[
                    (0, 1),
                    (1, 1),
                    (2, 0),
                    (3, 0),
                    (3, 1),
                    (4, 0),
                    (4, 1),
                    (5, 1),
                    (6, 0),
                    (7, 0),
                    (7, 1),
                    (8, 0),
                    (8, 1),
                    (9, 1),
                    (10, 0),
                    (11, 0),
                ],
            )

            result, group_2 = omni.kit.commands.execute(
                "RangeSensorCreateUltrasonicFiringGroup",
                path="/World/UltrasonicFiringGroup_1",
                emitter_modes=[(1, 1), (2, 0), (5, 1), (6, 0), (9, 1), (10, 0)],
                receiver_modes=[
                    (0, 1),
                    (1, 0),
                    (1, 1),
                    (2, 0),
                    (2, 1),
                    (3, 0),
                    (4, 1),
                    (5, 1),
                    (6, 0),
                    (7, 0),
                    (8, 1),
                    (9, 0),
                    (9, 1),
                    (10, 0),
                    (10, 1),
                    (11, 0),
                ],
            )
            self.ultrasonicPath = "/World/UltrasonicArray"

            result, self.ultrasonic = omni.kit.commands.execute(
                "RangeSensorCreateUltrasonicArray",
                path=self.ultrasonicPath,
                # Min and max range for the ULTRASONIC.  This defines the starting and stopping locations for the linetrace
                min_range=0.4,
                max_range=4.5,
                # These attributes affect drawing the ultrasonic in the viewport.  High Level Of Detail (HighLod) = True will draw
                # all rays.  If false it will only draw horizontal rays.  Draw Ultrasonic Points = True will draw the actual
                # ULTRASONIC rays in the viewport.
                draw_points=False,
                draw_lines=True,
                # Horizontal and vertical resolution in degrees.  Rays will be fired on the bin boundries defined by the
                # resolution.  If your FOV is 45 degrees and your resolution is 15 degrees, you will get rays at
                # 0, 15, 30, and 45 degrees.
                horizontal_fov=90.0,  # set wedge vertical extent in degrees
                vertical_fov=15.0,  # set wedge horizontal extent in degrees
                horizontal_resolution=0.3,
                vertical_resolution=0.5,
                num_bins=224,
                emitter_prims=emitter_paths,
                firing_group_prims=[group_1.GetPath(), group_2.GetPath()],
            )

            # we want to make sure we can see the ultrasonic we made, so we set the camera position and look target
            self._viewport.set_camera_position("/OmniverseKit_Persp", 500, 500, 500, True)
            self._viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)

    def _on_spawn_ultrasonic_button(self):
        # wait for new stage before creating ultrasonic
        task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._spawn_ultrasonic_function(task))

    def _on_spawn_obstacles_button(self):
        stage = omni.usd.get_context().get_stage()
        self.CubePath = "/World/Cube"
        self.CylinderPath = "/World/Cylinder"
        offset = Gf.Vec3f(-46.36036, 728.20291, 61.8376)
        offset_cylinder = Gf.Vec3f(384.92474, 205.46415, 68.68243)
        size = 100
        cylinder_height = 200
        radius = 10

        # Define a light so we can see the obstacle better
        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(500)

        # To create a cube, we first define our geometry at our chosen path.  Then, becuase
        # we will need the primitive later, we query the prim from the stage. If the prim already exists, skip creation
        if stage.GetPrimAtPath(self.CubePath):
            return

        cylinderGeom = UsdGeom.Cylinder.Define(stage, self.CylinderPath)
        cubeGeom = UsdGeom.Cube.Define(stage, self.CubePath)
        cubePrim = stage.GetPrimAtPath(self.CubePath)
        cylinderPrim = stage.GetPrimAtPath(self.CylinderPath)

        # Remember!  Attributes do not exist until they are created.  Here we set the value to the non defualt at
        # creation.  Note that moving the cube to a different location involves adding a translation operation to
        # our primitive.
        cubeGeom.CreateSizeAttr(size)
        cylinderGeom.CreateHeightAttr(cylinder_height)
        cylinderGeom.CreateRadiusAttr(radius)
        cubeGeom.AddTranslateOp().Set(offset)
        cylinderGeom.AddTranslateOp().Set(offset_cylinder)

        # In order for our cube to interact with the ULTRASONIC, it needs to be able to colide with our physX line traces.
        # to do this, we give our cube the collision API, and set it's material and collision group.
        collisionAPI = UsdPhysics.CollisionAPI.Apply(cubePrim)
        collisionAPI = UsdPhysics.CollisionAPI.Apply(cylinderPrim)
        defaultPrimPath = str(stage.GetDefaultPrim().GetPath())

    def _draw_envelope_frame(self):
        envelope_arr = self._ul.get_envelope_array(self.ultrasonicPath)

        with self._envelope_frame:
            with ui.VStack():
                ui.Label("Inspect Envelopes:", height=0)
                ui.Label("Mouse over the plot to see the associated envelope values per bin", height=0)
                for i in range(envelope_arr.shape[0]):
                    with ui.HStack():
                        ui.Label(f"{i}", width=15)
                        ui.Spacer(width=5)
                        ui.Plot(
                            ui.Type.HISTOGRAM,
                            0.0,
                            600.0,
                            *(envelope_arr[i].tolist()),
                            height=50,
                            style={"color": 0xFFFFFFFF},
                        )
                    ui.Spacer(height=1)

    def _get_info_function(self):
        maxDepth = self.ultrasonic.GetMaxRangeAttr().Get()

        # The ULTRASONIC itself exists as a C++ object.  In order to retrieve data from this object we need to call
        # C++ code, but this is handled for us through the use of python bindings.  Here we get the depth value of
        # each ray, and the spherical coordinates of each ray in (azimuth, zenith).
        depth = self._ul.get_depth_data(self.ultrasonicPath, 5)
        zenith = self._ul.get_zenith_data(self.ultrasonicPath)
        azimuth = self._ul.get_azimuth_data(self.ultrasonicPath)

        self._draw_envelope_frame()

        # most of the below is string formatting in order to display our data in a nice table within our GUI.
        tableString = ""
        numCols = len(zenith)
        rowString = ""
        for i in range(numCols):
            rowString += "{" + str(i + 2) + ":." + str(5) + "f}   "
        rowString = "{0:16}  {1:10}" + rowString + "\n"

        tableString += rowString.format("Azimuth \ Zenith", " | ", *zenith)
        tableString += "-" * len(tableString) + "\n"
        for row, cols in enumerate(depth):
            # The data on the c++ side is stored as uint16.  in order to get our depth values into centimeters, we
            # must first convert from uint16 into float on [0,1], and then scale to the maximum distance.
            entry = [ray * maxDepth / 65535.0 for ray in cols]
            tableString += rowString.format("{0:.5f}".format(azimuth[row]), " | ", *entry)

        self._info_label.text = tableString
