import omni
import omni.ui as omni_ui
from omni.isaac.range_sensor import _range_sensor
import omni.isaac.RangeSensorSchema as RangeSensorSchema
from pxr import Usd, UsdGeom, UsdLux, Sdf, Gf, UsdPhysics
from omni.physx.scripts.physicsUtils import *
import asyncio


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
        self._window = omni.kit.ui.Window(
            "Ultrasonic Info",
            300,
            200,
            menu_path="Isaac/Ultrasonic/Ultrasonic Demo App",
            open=False,
            dock=omni.kit.ui.DockPreference.LEFT_BOTTOM,
        )

        #  Kit GUIs are defined by a tree of layouts, and leaf layouts contain GUI elements (like buttons or
        # text entry fields).  You can learn more about Layouts and GUIs in the python manual at
        # Scripting API > omni.kit package > omni.kit.ui module.
        sublayout = self._window.layout.add_child(omni.kit.ui.ColumnLayout())

        # We are using a single colum layout, so these buttons will appear as a single column on
        # the left side of the window.
        sublayout.add_child(
            omni.kit.ui.Label(
                "This sample demonstrates how to create an ultrasonic sensor, set properties and get data from it. Press play once the sensor is created to simulate"
            )
        )

        spawn_ultrasonic_button = sublayout.add_child(omni.kit.ui.Button("Clean Stage And Spawn an Ultrasonic Sensor"))
        spawn_ultrasonic_button.tooltip = omni.kit.ui.Label(
            "Spawn an Ultrasonic Sensor in the Stage and set its properties"
        )
        spawn_obstacles_button = sublayout.add_child(omni.kit.ui.Button("Spawn an Obstacle for the Ultrasonic Sensor"))
        spawn_obstacles_button.tooltip = omni.kit.ui.Label("Spawn an obstacle and move camera so its in view")
        get_info_button = sublayout.add_child(
            omni.kit.ui.Button("Get data from the Ultrasonic Sensor (press play first)")
        )
        get_info_button.tooltip = omni.kit.ui.Label(
            "Press play to enable simulation and then press this button to get the current ultrasonic information"
        )
        sublayout.add_child(
            omni.kit.ui.Label(
                'Note: The buttons above only work with the ultrasonic spawned by the "Spawn an Ultrasonic Sensor" button and not existing ones in the stage'
            )
        )

        # When you interact with a GUI element, you are interacting with a kit Widget.  A widget is a single
        # GUI element that may or may not contain functions you can use to define how to interact with that widget.
        # In this case, we are making simple button widgets, which will call a function we define whenever we click it.
        spawn_ultrasonic_button.set_clicked_fn(self._on_spawn_ultrasonic_button)
        spawn_obstacles_button.set_clicked_fn(self._on_spawn_obstacles_button)
        get_info_button.set_clicked_fn(self._get_info_function)

        # The separator is an example of a widget that does not contain any interactive functionality.  I simply puts
        # a tiny gap in the UI in order separate one part from another.
        sublayout.add_child(omni.kit.ui.Separator())

        # we add a scrolling frame because we also want to display information about our ULTRASONIC, and the amount
        # of information we display depends on the ULTRASONIC parameters.
        scrolling_frame = sublayout.add_child(omni.kit.ui.ScrollingFrame("", -1, -1))
        self.info_label = scrolling_frame.add_child(
            omni.kit.ui.Label("", useclipboard=True, clippingmode=omni.kit.ui.ClippingType.WRAP)
        )

    def on_shutdown(self):
        # Perform cleanup once the sample closes
        self._window = None

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
            emitter_poses = [
                Gf.Matrix4d(Gf.Rotation(Gf.Quatd(0.951057, 0, 0, -0.309017)), Gf.Vec3d(25, 0.0, 25)),
                Gf.Matrix4d(Gf.Rotation(Gf.Quatd(0.987688, 0, 0, -0.156434)), Gf.Vec3d(25, 50.0, 25)),
                Gf.Matrix4d(Gf.Rotation(Gf.Quatd(0.987688, 0, 0, 0.156434)), Gf.Vec3d(25, 100, 25)),
                Gf.Matrix4d(Gf.Rotation(Gf.Quatd(0.951057, 0, 0, 0.309017)), Gf.Vec3d(25, 150, 25)),
                Gf.Matrix4d(Gf.Rotation(Gf.Quatd(-0.309017, 0, 0, 0.951056)), Gf.Vec3d(-25, 0.0, 25)),
                Gf.Matrix4d(Gf.Rotation(Gf.Quatd(-0.156435, 0, 0, 0.987688)), Gf.Vec3d(-25, 50.0, 25)),
                Gf.Matrix4d(Gf.Rotation(Gf.Quatd(0.156434, 0, 0, 0.987688)), Gf.Vec3d(-25, 100, 25)),
                Gf.Matrix4d(Gf.Rotation(Gf.Quatd(0.309017, 0, 0, 0.951057)), Gf.Vec3d(-25, 150, 25)),
                Gf.Matrix4d(Gf.Rotation(Gf.Quatd(0.760406, 0, 0, -0.649448)), Gf.Vec3d(12.5, 0.0, 25)),
                Gf.Matrix4d(Gf.Rotation(Gf.Quatd(0.649448, 0, 0, -0.760406)), Gf.Vec3d(12.5, 0.0, 25)),
                Gf.Matrix4d(Gf.Rotation(Gf.Quatd(0.760406, 0, 0, 0.649448)), Gf.Vec3d(12.5, 150, 25)),
                Gf.Matrix4d(Gf.Rotation(Gf.Quatd(0.649448, 0, 0, 0.760406)), Gf.Vec3d(12.5, 150, 25)),
            ]

            emitters = []
            for pose in emitter_poses:
                result, emitter_prim = omni.kit.commands.execute(
                    "CreateRangeSensorUltrasonicEmitterCommand",
                    path="/World/UltrasonicEmitter",
                    per_ray_intensity=0.4,
                    yaw_offset=0.0,
                    firing_delay=0.5,
                )

                emitter_prim.GetPrim().GetAttribute("xformOp:transform").Set(pose)
                emitters.append(emitter_prim)

            # create the ULTRASONIC.  Before we can set any attributes on our ULTRASONIC, we must first create the prim using our
            # ULTRASONIC schema, and then populate it with the parameters we will be manipulating.  If you try to manipulate
            # a parameter before creating it, you will get a runtime error

            emitter_paths = [emitter.GetPath() for emitter in emitters]

            self.ultrasonicPath = "/World/UltrasonicArray"

            result, self.ultrasonic = omni.kit.commands.execute(
                "CreateRangeSensorUltrasonicArrayCommand",
                path=self.ultrasonicPath,
                # Min and max range for the ULTRASONIC.  This defines the starting and stopping locations for the linetrace
                min_range=0.4,
                max_range=3.0,
                # These attributes affect drawing the ultrasonic in the viewport.  High Level Of Detail (HighLod) = True will draw
                # all rays.  If false it will only draw horizontal rays.  Draw Ultrasonic Points = True will draw the actual
                # ULTRASONIC rays in the viewport.
                draw_points=False,
                draw_lines=True,
                # Horizontal and vertical resolution in degrees.  Rays will be fired on the bin boundries defined by the
                # resolution.  If your FOV is 45 degrees and your resolution is 15 degrees, you will get rays at
                # 0, 15, 30, and 45 degrees.
                horizontal_fov=15.0,  # set wedge vertical extent in degrees
                vertical_fov=10.0,  # set wedge horizontal extent in degrees
                horizontal_resolution=0.5,
                vertical_resolution=0.5,
                pulse_duration=0.1,
                pulse_gap_delta=0.3,
                num_bins=224,
                emitter_prims=emitter_paths,
            )

            # we want to make sure we can see the ultrasonic we made, so we set the camera position and look target
            self._viewport.set_camera_position("/OmniverseKit_Persp", 500, 500, 500, True)
            self._viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)

    def _on_spawn_ultrasonic_button(self, widget):
        # wait for new stage before creating ultrasonic
        task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._spawn_ultrasonic_function(task))

    def _on_spawn_obstacles_button(self, widget):
        stage = omni.usd.get_context().get_stage()
        self.CubePath = "/World/Cube"
        offset = Gf.Vec3f(-200.0, 0.0, 50.0)
        size = 100

        # Define a light so we can see the obstacle better
        distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
        distantLight.CreateIntensityAttr(500)

        # To create a cube, we first define our geometry at our chosen path.  Then, becuase
        # we will need the primitive later, we query the prim from the stage. If the prim already exists, skip creation
        if stage.GetPrimAtPath(self.CubePath):
            return
        cubeGeom = UsdGeom.Cube.Define(stage, self.CubePath)
        cubePrim = stage.GetPrimAtPath(self.CubePath)

        # Remember!  Attributes do not exist until they are created.  Here we set the value to the non defualt at
        # creation.  Note that moving the cube to a different location involves adding a translation operation to
        # our primitive.
        cubeGeom.CreateSizeAttr(size)
        cubeGeom.AddTranslateOp().Set(offset)

        # In order for our cube to interact with the ULTRASONIC, it needs to be able to colide with our physX line traces.
        # to do this, we give our cube the collision API, and set it's material and collision group.
        collisionAPI = UsdPhysics.CollisionAPI.Apply(cubePrim)
        defaultPrimPath = str(stage.GetDefaultPrim().GetPath())

    def _get_info_function(self, widget):
        maxDepth = self.ultrasonic.GetMaxRangeAttr().Get()

        # The ULTRASONIC itself exists as a C++ object.  In order to retrieve data from this object we need to call
        # C++ code, but this is handled for us through the use of python bindings.  Here we get the depth value of
        # each ray, and the spherical coordinates of each ray in (azimuth, zenith).
        depth = self._ul.get_depth_data(self.ultrasonicPath, 5)
        zenith = self._ul.get_zenith_data(self.ultrasonicPath)
        azimuth = self._ul.get_azimuth_data(self.ultrasonicPath)
        envelope_arr = self._ul.get_envelope_array(self.ultrasonicPath)

        self.plot_window = omni_ui.Window("Inspect Envelopes", width=385, height=620, visible=True)
        with self.plot_window.frame:
            with omni_ui.VStack():
                for i in range(envelope_arr.shape[0]):
                    omni_ui.Plot(
                        omni_ui.Type.HISTOGRAM,
                        0.0,
                        600.0,
                        *(envelope_arr[i].tolist()),
                        width=360,
                        height=50,
                        style={"color": 0xFFFF0000},
                    )
                    omni_ui.Spacer(height=1)

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

        self.info_label.text = tableString
