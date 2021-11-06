# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from scene.asset import Object


class RoomFace(Object):
    """ For managing an Xform asset in Isaac Sim. """

    def __init__(self, sim_app, sim_context, path, prefix, coord, rotation, scaling):
        """ Construct Object. """

        self.coord = coord
        self.rotation = rotation
        self.scaling = scaling

        super().__init__(sim_app, sim_context, "", path, prefix, None, None)

    def load_asset(self):
        """ Create asset from object parameters. """

        import omni.kit.commands
        from omni.isaac.core.prims import XFormPrim
        from pxr import Gf, PhysicsSchemaTools, Sdf

        if self.prefix == "floor":
            # Create invisible ground plane
            size = self.scaling[0] * 100
            path = "/World/Room/ground"
            PhysicsSchemaTools.addGroundPlane(self.stage, path, "Z", size, Gf.Vec3f(0, 0, 0), Gf.Vec3f(1))
            omni.kit.commands.execute("ToggleVisibilitySelectedPrims", selected_paths=[Sdf.Path(path)])

        # Create plane
        omni.kit.commands.execute("CreateMeshPrimWithDefaultXform", prim_type="Plane")
        omni.kit.commands.execute("MovePrim", path_from="/Plane", path_to=self.path)

        self.prim = self.stage.GetPrimAtPath(self.path)
        self.xform_prim = XFormPrim(self.path)

    def place_in_scene(self):
        """ Scale, rotate, and translate asset. """

        self.translate(self.coord)
        self.rotate(self.rotation)
        self.scale(self.scaling)

    def step(self):
        """ Room Face does not update in a scene's sequence. """

        return
