import omni
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from omni.isaac.range_sensor import _range_sensor
import omni.isaac.RangeSensorSchema as RangeSensorSchema
from pxr import Usd, UsdGeom, UsdLux, Sdf, Gf, UsdPhysics
import asyncio
import weakref

EXTENSION_NAME = "LIDAR Info"


class Extension(omni.ext.IExt):
    def on_startup(self):
        """
        This sample is written to demonstrate the LIDAR python API for Isaac Sim.
        """

        # The extension acquires the LIDAR interface at startup.  It will be released during extension shutdown.  We
        # create a LIDAR prim using our schema, and then we interact with / query that prim using the python API found
        # in lidar/bindings
        self._li = _range_sensor.acquire_lidar_sensor_interface()

        # We also need an interface to the viewport to do things like set and get camera positions
        self._viewport = omni.kit.viewport.get_default_viewport_window()

        # This just defines the window we will use to access the lidar_info GUI.  Note that clicking on the menu item
        # does not create an instance of lidar_info; that is done by the extension when it is loaded by kit.  All this
        # menu does is show or hide our GUI we will use for interacting with lidar_info
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
        add_menu_items(self._menu_items, "Isaac Samples")

        # Kit GUIs are defined by a tree of layouts, and leaf layouts contain GUI elements (like buttons or
        # text entry fields).  You can learn more about Layouts and GUIs in the python manual at
        # Scripting API > omni.kit package > omni.ui module.
        # Each button below has a tooltip and a function that is called when the button is clicked
        with self._window.frame:
            with ui.VStack():
                ui.Label(
                    "This sample demonstrates how to create a LIDAR, set properties and get data from it. Press play once LIDAR is created to simulate",
                    height=0,
                    word_wrap=True,
                )
                ui.Button(
                    "Clean Stage And Spawn a LIDAR Sensor",
                    clicked_fn=self._on_spawn_lidar_button,
                    tooltip="Spawn an LIDAR Sensor in the Stage and set its properties",
                    height=0,
                )
                ui.Button(
                    "Spawn an Obstacle for the LIDAR Sensor",
                    clicked_fn=self._on_spawn_obstacles_button,
                    tooltip="Spawn an obstacle and move camera so its in view",
                    height=0,
                )
                ui.Button(
                    "Get data from the LIDAR Sensor (press play first)",
                    clicked_fn=self._get_info_function,
                    tooltip="Press play to enable simulation and then press this button to get the current LIDAR information",
                    height=0,
                )
                ui.Label(
                    'Note: The buttons above only work with the LIDAR spawned by the "Spawn an LIDAR Sensor" button and not existing ones in the stage',
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

    def on_shutdown(self):
        # Perform cleanup once the sample closes
        remove_menu_items(self._menu_items, "Isaac Samples")
        self._window = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    async def _spawn_lidar_function(self, task):
        # Wait for stage clear to complete before creating LIDAR
        done, pending = await asyncio.wait({task})
        if task in done:
            stage = omni.usd.get_context().get_stage()

            # Set up axis to z.  The LIDAR extension scans in the XZ plane, which is assumed to be perpendicular to the
            # rotational plane, and so to use the LIDAR as it is currently written, Z must be up.
            UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
            UsdGeom.SetStageMetersPerUnit(stage, 0.01)

            # Create the PhysicsScene.  The lidar is going to execute line trace calls in PhysX, and return a value based
            # on how far it travels before colliding with an object that is using the PhysX collision API.  Because of this,
            # to use the LIDAR extension, you MUST have a physics scene defined
            UsdPhysics.Scene.Define(stage, Sdf.Path("/World/physicsScene"))

            # create the LIDAR.  Before we can set any attributes on our LIDAR, we must first create the prim using our
            # LIDAR schema, and then populate it with the parameters we will be manipulating.  If you try to manipulate
            # a parameter before creating it, you will get a runtime error
            self.lidarPath = "/World/Lidar"
            self.lidar = RangeSensorSchema.Lidar.Define(stage, Sdf.Path(self.lidarPath))

            # Horizontal and vertical field of view in degrees
            self.lidar.CreateHorizontalFovAttr().Set(360.0)
            self.lidar.CreateVerticalFovAttr().Set(10)

            # Rotation rate in Hz
            self.lidar.CreateRotationRateAttr().Set(20.0)

            # Horizontal and vertical resolution in degrees.  Rays will be fired on the bin boundries defined by the
            # resolution.  If your FOV is 45 degrees and your resolution is 15 degrees, you will get rays at
            # 0, 15, 30, and 45 degrees.
            self.lidar.CreateHorizontalResolutionAttr().Set(1.0)
            self.lidar.CreateVerticalResolutionAttr().Set(1.0)

            # Min and max range for the LIDAR.  This defines the starting and stopping locations for the linetrace
            self.lidar.CreateMinRangeAttr().Set(0.4)
            self.lidar.CreateMaxRangeAttr().Set(100.0)

            # These attributes affect drawing the lidar in the viewport.  High Level Of Detail (HighLod) = True will draw
            # all rays.  If false it will only draw horizontal rays.  Draw Lidar Points = True will draw the actual
            # LIDAR rays in the viewport.
            self.lidar.CreateHighLodAttr().Set(True)
            self.lidar.CreateDrawPointsAttr().Set(False)
            self.lidar.CreateDrawLinesAttr().Set(False)

            # We set the attributes we created.  We could have just set the attributes at creation, but this was
            # more illustrative.  It's important to remember that attributes do not exist until you create them; even
            # if they are defined in the schema.
            self.lidar.GetRotationRateAttr().Set(0.5)
            self.lidar.GetDrawLinesAttr().Set(True)
            self.lidar.AddTranslateOp().Set(Gf.Vec3f(0.0, 0.0, 25.0))

            # we want to make sure we can see the lidar we made, so we set the camera position and look target
            self._viewport.set_camera_position("/OmniverseKit_Persp", 500, 500, 500, True)
            self._viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)

    def _on_spawn_lidar_button(self):
        # wait for new stage before creating lidar
        task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._spawn_lidar_function(task))

    def _on_spawn_obstacles_button(self):
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

        # In order for our cube to interact with the LIDAR, it needs to be able to colide with our physX line traces.
        # to do this, we give our cube the collision API, and set it's material and collision group.
        collisionAPI = UsdPhysics.CollisionAPI.Apply(cubePrim)

    def _get_info_function(self):
        maxDepth = self.lidar.GetMaxRangeAttr().Get()

        # The LIDAR itself exists as a C++ object.  In order to retrieve data from this object we need to call
        # C++ code, but this is handled for us through the use of python bindings.  Here we get the depth value of
        # each ray, and the spherical coordinates of each ray in (azimuth, zenith).
        depth = self._li.get_depth_data(self.lidarPath)
        zenith = self._li.get_zenith_data(self.lidarPath)
        azimuth = self._li.get_azimuth_data(self.lidarPath)

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
