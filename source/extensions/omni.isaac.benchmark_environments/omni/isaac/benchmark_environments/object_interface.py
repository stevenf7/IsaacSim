# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from omni.client import delete
from pxr import UsdGeom, Gf, UsdPhysics
import numpy as np
import asyncio
import uuid
import omni.kit.app
from omni.isaac.core.utils.prims import delete_prim


def get_Gf_transform(translation, rotation):
    """
    This function converts from np arrays to a Gf.Matrix4d object.  
    """

    rot_mat = Gf.Matrix3d()
    for i in range(3):
        rot_mat.SetColumn(i, Gf.Vec3d(*rotation[i].astype(np.float64)))

    trans = Gf.Vec3d(*translation.astype(np.float64))

    mat = Gf.Matrix4d()
    mat.SetTranslate(trans)
    mat.SetRotateOnly(rot_mat)

    return mat


class Object:
    """
    An Object is a collection of prims that move and change their properties together.  A base Object has no prims
    in it by default because the construct method is empty.  The Object Class is inherited by specific types of 
    objects in objects.py and the construct function is implemented

    Objects have a base translation and rotation.  All prims that form the object have a 
        (fixed) translation and rotation that is relative to the base.  The base pose can 
        be updated with set_base_pose, and the world coordinate positions of every prim will
        be updated by their relative position to the base.

    Objects have two lists of prims: self.components, and self.targets
        self.components: prims that for the object that the robot must avoid
        self.targets: possible targets to make a robot seek. Ex. the cubby object has possible targets
            in each cubby that are transformed along with the base. A random target can be retrieved with
            self.get_random_target() 

    Objects are made up of three primitives: capsules, spheres, and rectangular prisms
    TODO: allow meshes to be loaded for an object
    """

    def __init__(self, _stage, base_translation, base_rotation, color=Gf.Vec3f(1.0, 1.0, 0), **kwargs):
        self._stage = _stage

        self.initial_base_trans = base_translation
        self.initial_base_rotation = base_rotation
        self.base_pose = get_Gf_transform(base_translation, base_rotation)
        self.components = []
        self.color = color

        self.targets = []
        self.last_target = None

        # make a random USD path for all the prims in this object
        object_id = str(uuid.uuid4())
        self.base_path = ("/scene/object-" + object_id + "-").replace("-", "_")
        self.target_path = ("/scene/target-" + object_id + "-").replace("-", "_")

        self.prim2pose_rel = {}  # pose of each component relative to the base

        self.construct(**kwargs)

    def construct(self, **kwargs):
        pass

    def get_random_target(self, make_visible=True):
        if self.last_target is not None:
            self.last_target.MakeInvisible()

        if len(self.targets) > 0:
            target = np.random.choice(self.targets)
            if make_visible:
                target.MakeVisible()
            self.last_target = target
            return target

    def get_all_prims(self):
        # get all prims that the robot should avoid
        return [com.GetPrim() for com in self.components]

    def create_target(
        self,
        relative_translation=np.zeros(3),
        relative_rotation=None,
        target_color=Gf.Vec3f(1.0, 0.0, 0.0),
        target_size=5,
    ):

        path = self.target_path + str(len(self.targets))
        geom = UsdGeom.Cube.Define(self._stage, path)

        if relative_rotation is None:
            rel_pose = Gf.Vec4d(*relative_translation.astype(np.float64), 1)
            abs_pos = Gf.Vec3d(*list(rel_pose * self.base_pose)[:3])
            geom.AddTranslateOp().Set(abs_pos)
        else:
            rel_pose = get_Gf_transform(relative_translation, relative_rotation)
            geom.AddTransformOp().Set(rel_pose * self.base_pose)
        self.prim2pose_rel[geom] = rel_pose

        geom.CreateSizeAttr(target_size)

        geom.CreateDisplayColorAttr().Set([target_color])
        geom.GetPrim().SetCustomDataByKey("type", "target")

        geom.MakeInvisible()

        self.targets.append(geom)

        return geom

    def create_block(self, size, scales, relative_translation=np.zeros(3), relative_rotation=np.eye(3)):
        path = self.base_path + str(len(self.components))
        geom = UsdGeom.Cube.Define(self._stage, path)

        rel_pose = get_Gf_transform(relative_translation, relative_rotation)
        self.prim2pose_rel[geom] = rel_pose

        geom.AddTransformOp().Set(rel_pose * self.base_pose)

        geom.CreateSizeAttr(size)
        scales = Gf.Vec3f(scales[0], scales[1], scales[2])
        geom.AddScaleOp().Set(scales)

        geom.CreateDisplayColorAttr().Set([self.color])
        geom.GetPrim().SetCustomDataByKey("type", "box")

        self.components.append(geom)

        return geom

    def create_sphere(self, radius, relative_translation=np.zeros(3), relative_rotation=np.eye(3)):
        path = self.base_path + str(len(self.components))
        geom = UsdGeom.Sphere.Define(self._stage, path)
        geom.CreateRadiusAttr(radius)

        geom.CreateDisplayColorAttr().Set([self.color])

        rel_pose = get_Gf_transform(relative_translation, relative_rotation)

        self.prim2pose_rel[geom] = rel_pose

        geom.AddTransformOp().Set(rel_pose * self.base_pose)
        geom.GetPrim().SetCustomDataByKey("type", "sphere")

        self.components.append(geom)

        return geom

    def create_capsule(self, radius, height, relative_translation=np.zeros(3), relative_rotation=np.eye(3)):
        path = self.base_path + str(len(self.components))
        geom = UsdGeom.Capsule.Define(self._stage, path)
        geom.CreateRadiusAttr(radius)
        geom.CreateHeightAttr(height)

        geom.CreateDisplayColorAttr().Set([self.color])

        rel_pose = get_Gf_transform(relative_translation, relative_rotation)

        self.prim2pose_rel[geom] = rel_pose

        geom.AddTransformOp().Set(rel_pose * self.base_pose)
        geom.GetPrim().SetCustomDataByKey("type", "capsule")

        self.components.append(geom)

        return geom

    def set_base_pose(self, translation=np.zeros(3), rotation=np.eye(3)):
        self.base_pose = get_Gf_transform(translation, rotation)

        for component in self.components:
            component.GetPrim().GetAttribute("xformOp:transform").Set(self.prim2pose_rel[component] * self.base_pose)

        for target in self.targets:
            target_prim = target.GetPrim()
            if target_prim.HasAttribute("xformOp:transform"):
                target_prim.GetAttribute("xformOp:transform").Set(self.prim2pose_rel[target] * self.base_pose)
            else:
                rel_pos = self.prim2pose_rel[target]
                abs_pos = Gf.Vec3d(*list(rel_pos * self.base_pose)[:3])
                target_prim.GetAttribute("xformOp:translate").Set(abs_pos)

    def set_color(self, color):
        self.color = color
        for component in self.components:
            components.GetDisplayColorAttr().Set([self.color])

    def set_visibility(self, on=True):
        for component in self.components:
            if on:
                component.MakeVisible()
            else:
                component.MakeInvisible()

    def set_physics_properties(self, enable_rigid_body=True, enable_collisions=True, mass=1e-7):
        """
        Args:
            enable_rigid_body: Register all prims in this Object as rigid bodies for physics purposes.
                enables gravity
                lets body be pushed upon collision
            enable_collisions: Turn on collision physics for all prims in this Object
            mass: Mass affects collision physics for this Object if both enable_rigid_body and enable_collisions
                are true.  The default mass is negligible (this Object will not impede the robot at all).

            Registering the prim as a rigid body without turning on collisions will cause the Object to
            fall through the ground unless its position is otherwise set using set_base_pose()

            Enabling only collisions will make this Object become impassable for the robot
        """

        # async def set_physics_properties_async():
        # await omni.kit.app.get_app().next_update_async()
        for component in self.components:
            if enable_rigid_body:
                UsdPhysics.RigidBodyAPI.Apply(component.GetPrim())
                # await omni.kit.app.get_app().next_update_async()
            if enable_collisions:
                UsdPhysics.CollisionAPI.Apply(component.GetPrim())
                # await omni.kit.app.get_app().next_update_async()
            massAPI = UsdPhysics.MassAPI.Apply(component.GetPrim())
            massAPI.CreateMassAttr(mass)
            # await omni.kit.app.get_app().next_update_async()

        # asyncio.ensure_future(set_physics_properties_async())

    def delete(self):
        for component in self.components:
            delete_prim(component.GetPath())
        self.components = []

        for target in self.targets:
            delete_prim(target.GetPath())

        self.targets = []

    def reset(self):
        self.set_base_pose(self.initial_base_trans, self.initial_base_rotation)
        for target in self.targets:
            target.MakeInvisible()
