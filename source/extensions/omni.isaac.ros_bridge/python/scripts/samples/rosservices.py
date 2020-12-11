# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# This is an example script showing how to use rosbridge to publish joint_states of an articulated robot

from pxr import Sdf, Gf, UsdGeom, UsdLux
import omni.usd
import omni
import omni.kit.ui
import omni.kit.editor
import omni.isaac.RosBridgeSchema as ROSSchema
import asyncio


class Extension(omni.ext.IExt):
    def on_startup(self):
        # setting up the UI on the menu bar for this example
        self._window = omni.kit.ui.Window(
            "Rosservices",
            300,
            200,
            menu_path="Isaac/ROS/Rosservices",
            open=False,
            dock=omni.kit.ui.DockPreference.LEFT_BOTTOM,
        )
        sublayout = self._window.layout.add_child(omni.kit.ui.ColumnLayout())

        clean_stage_btn = sublayout.add_child(omni.kit.ui.Button("Clean Stage"))
        clean_stage_btn.set_clicked_fn(self._on_clean_stage)
        clean_stage_btn.tooltip = omni.kit.ui.Label("Clean the stage")

        add_cube_btn = sublayout.add_child(omni.kit.ui.Button("Add Cube"))
        add_cube_btn.set_clicked_fn(self._on_add_cube)
        add_cube_btn.tooltip = omni.kit.ui.Label("Add a Cube and start its pose service")

        add_cone_btn = sublayout.add_child(omni.kit.ui.Button("Add Cone"))
        add_cone_btn.set_clicked_fn(self._on_add_cone)
        add_cone_btn.tooltip = omni.kit.ui.Label("Add a Cone and start a second pose service")

        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._viewport.set_camera_position("/OmniverseKit_Persp", 103.4, 13.8, 19.8, True)
        self._viewport.set_camera_target("/OmniverseKit_Persp", -225.0, -23.78, -26.17, True)
        self._timeline = omni.timeline.get_timeline_interface()

    def on_shutdown(self):
        self._window = None

    def _on_clean_stage(self, widget):
        load_stage = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._load_stage(load_stage))

    async def _load_stage(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            self._stage = omni.usd.get_context().get_stage()
            # create some lighting
            distantLight = UsdLux.DistantLight.Define(self._stage, Sdf.Path("/World/defaultLight"))
            distantLight.CreateIntensityAttr(500)
            self._viewport.set_camera_position("/OmniverseKit_Persp", 103.4, 13.8, 19.8, True)
            self._viewport.set_camera_target("/OmniverseKit_Persp", -225.0, -23.78, -26.17, True)

    # add cube
    def _on_add_cube(self, widget):
        # create a cube
        self._stage = omni.usd.get_context().get_stage()
        distantLight = UsdLux.DistantLight.Define(self._stage, Sdf.Path("/World/defaultLight"))
        distantLight.CreateIntensityAttr(3000)
        CubePath = "/Cube"
        # position in space
        cube_pos = Gf.Vec3f(0.0, 0.0, 0.0)
        size = 10  # cm
        cubeGeom = UsdGeom.Cube.Define(self._stage, CubePath)
        cubeGeom.CreateSizeAttr(size)
        cubeGeom.AddTranslateOp().Set(cube_pos)

        # start its own pose service
        prim = ROSSchema.RosTeleport.Define(self._stage, Sdf.Path("/ROS_Teleport"))
        prim.CreateEnabledAttr(True)
        prim.CreatePoseSrvTopicAttr("/teleport_pos")
        prim.CreateTeleportPrimsRel()

        # connect the service to the cube prim
        ROS_prim = self._stage.GetPrimAtPath("/ROS_Teleport")
        ROS_prim.GetRelationship("teleportPrims").AddTarget(Sdf.Path("/Cube"))

        # make sure editor is playing for sending and receiving ros messages
        if not self._timeline.is_playing():
            self._timeline.play()

    # add cone
    def _on_add_cone(self, widget):
        # create a cube
        self._stage = omni.usd.get_context().get_stage()
        ConePath = "/Cone"
        # position in space
        cone_pos = Gf.Vec3f(10.0, -10.0, 10.0)
        radius = 6  # cm
        height = 12
        coneGeom = UsdGeom.Cone.Define(self._stage, ConePath)
        coneGeom.CreateRadiusAttr().Set(radius)
        coneGeom.CreateHeightAttr().Set(height)
        coneGeom.AddTranslateOp().Set(cone_pos)

        # start its own pose service
        prim = ROSSchema.RosTeleport.Define(self._stage, Sdf.Path("/ROS_Teleport_Cone"))
        prim.CreateEnabledAttr(True)
        prim.CreatePoseSrvTopicAttr("/teleport_pos_cone")
        prim.CreateTeleportPrimsRel()

        # connect the service to the cube prim
        ROS_prim = self._stage.GetPrimAtPath("/ROS_Teleport_Cone")
        ROS_prim.GetRelationship("teleportPrims").AddTarget(Sdf.Path("/Cone"))

        # make sure editor is playing for sending and receiving ros messages
        if not self._timeline.is_playing():
            self._timeline.play()
