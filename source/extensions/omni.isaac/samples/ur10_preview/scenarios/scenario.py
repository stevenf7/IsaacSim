#!/usr/bin/env python
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from pxr import Usd, UsdGeom, Sdf, Gf, PhysicsSchema, PhysxSchema
import omni.usd
import omni.kit.connectionhub

import numpy as np
import gc


def setTranslate(prim, new_loc):
    properties = prim.GetPropertyNames()
    if "xformOp:translate" in properties:
        translate_attr = prim.GetAttribute("xformOp:translate")

        translate_attr.Set(new_loc)
    elif "xformOp:translation" in properties:
        translation_attr = prim.GetAttribute("xformOp:translate")
        translation_attr.Set(new_loc)
    elif "xformOp:transform" in properties:
        transform_attr = prim.GetAttribute("xformOp:transform")
        matrix = prim.GetAttribute("xformOp:transform").Get()
        matrix.SetTranslateOnly(new_loc)
        transform_attr.Set(matrix)
    else:
        xform = UsdGeom.Xformable(prim)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
        xform_op.Set(Gf.Matrix4d().SetTranslate(new_loc))


def setRotate(prim, rot_mat):
    properties = prim.GetPropertyNames()
    if "xformOp:rotate" in properties:
        rotate_attr = prim.GetAttribute("xformOp:rotate")
        rotate_attr.Set(rot_mat)
    elif "xformOp:transform" in properties:
        transform_attr = prim.GetAttribute("xformOp:transform")
        matrix = prim.GetAttribute("xformOp:transform").Get()
        matrix.SetRotateOnly(rot_mat.ExtractRotation())
        transform_attr.Set(matrix)
    else:
        xform = UsdGeom.Xformable(prim)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
        xform_op.Set(Gf.Matrix4d().SetRotate(rot_mat))


def setCollisionGroup(prim, group):
    collisionAPI = PhysicsSchema.CollisionAPI.Apply(prim)
    rel = collisionAPI.CreateCollisionGroupRel()
    rel.AddTarget(Sdf.Path(group))


def setCollisionGroupUR10(stage, prim_path, group_path, is_ghost):
    print(prim_path)
    setCollisionGroup(stage.GetPrimAtPath(prim_path + "/base_link/Cylinder"), group_path)
    setCollisionGroup(stage.GetPrimAtPath(prim_path + "/shoulder_link/Cylinder"), group_path)
    setCollisionGroup(stage.GetPrimAtPath(prim_path + "/upper_arm_link/Cylinder"), group_path)
    setCollisionGroup(stage.GetPrimAtPath(prim_path + "/upper_arm_link/Cylinder_01"), group_path)
    setCollisionGroup(stage.GetPrimAtPath(prim_path + "/upper_arm_link/Cylinder_02"), group_path)
    setCollisionGroup(stage.GetPrimAtPath(prim_path + "/forearm_link/Cylinder"), group_path)
    setCollisionGroup(stage.GetPrimAtPath(prim_path + "/forearm_link/Cylinder_01"), group_path)
    setCollisionGroup(stage.GetPrimAtPath(prim_path + "/forearm_link/Cylinder_02"), group_path)
    setCollisionGroup(stage.GetPrimAtPath(prim_path + "/wrist_1_link/Cylinder"), group_path)
    setCollisionGroup(stage.GetPrimAtPath(prim_path + "/wrist_2_link/Cylinder"), group_path)
    setCollisionGroup(stage.GetPrimAtPath(prim_path + "/wrist_3_link/Cylinder"), group_path)
    for p in stage.GetPrimAtPath(prim_path + "/ee_link/collision").GetChildren():
        setCollisionGroup(p, group_path)
    # setCollisionGroup(stage.GetPrimAtPath(prim_path + "/ee_link/box"), group_path)


# def setCollisionGroupUR10(stage, prim_path, group_path, is_ghost):
#     print(prim_path)
#     setCollisionGroup(stage.GetPrimAtPath(prim_path + "/base_link/base_stl"), group_path)
#     setCollisionGroup(stage.GetPrimAtPath(prim_path + "/shoulder_link/shoulder_stl"), group_path)
#     setCollisionGroup(stage.GetPrimAtPath(prim_path + "/upper_arm_link/upper_arm_stl"), group_path)
#     setCollisionGroup(stage.GetPrimAtPath(prim_path + "/forearm_link/forearm_stl"), group_path)
#     setCollisionGroup(stage.GetPrimAtPath(prim_path + "/wrist_1_link/wrist_1_stl"), group_path)
#     setCollisionGroup(stage.GetPrimAtPath(prim_path + "/wrist_2_link/wrist_2_stl"), group_path)
#     setCollisionGroup(stage.GetPrimAtPath(prim_path + "/wrist_3_link/wrist_3_stl"), group_path)
#     for p in stage.GetPrimAtPath(prim_path + "/ee_link/suction_cup").GetChildren():
#         setCollisionGroup(p, group_path)
#     # setCollisionGroup(stage.GetPrimAtPath(prim_path + "/ee_link/box"), group_path)


def setUpZAxis(stage):
    rootLayer = stage.GetRootLayer()
    rootLayer.SetPermissionToEdit(True)
    with Usd.EditContext(stage, rootLayer):
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)


def CreateSolidUR10(stage, env_path, UR10_stage, solid_robot, location):
    envPrim = stage.DefinePrim(env_path, "Xform")
    envPrim.GetReferences().AddReference(UR10_stage)
    setTranslate(envPrim, location)
    print(env_path + "/ur10", solid_robot)
    setCollisionGroupUR10(stage, env_path + "/ur10", solid_robot, False)


def CreateGhostUR10(stage, env_path, UR10_ghost_usd, ghost_robot, ghost_index):
    ghost_path = env_path + "/Ghost/robot_{}".format(ghost_index)
    ghostPrim = stage.DefinePrim(ghost_path, "Xform")
    ghostPrim.GetReferences().AddReference(UR10_ghost_usd)
    setTranslate(ghostPrim, Gf.Vec3d(0, 0, 0))
    imageable = UsdGeom.Imageable(ghostPrim)
    if imageable:
        imageable.MakeInvisible()
    setCollisionGroupUR10(stage, ghost_path + "/ur10", ghost_robot, True)


def CreateObjects(stage, asset_paths, env_paths, poses):
    if (len(asset_paths) != len(env_paths)) and len(asset_paths) != len(poses):
        print("Error: asset paths, env paths and poses must be same length")
        return
    for (asset, path, pose) in zip(*[asset_paths, env_paths, poses]):
        prim = stage.DefinePrim(path, "Xform")
        prim.GetReferences().AddReference(asset)
        setTranslate(prim, pose)
        print(prim.GetPath().pathString)


def CreateRubiksCube(stage, asset_path, prim_path, location):
    obstaclePrim = stage.DefinePrim(prim_path, "Xform")
    obstaclePrim.GetReferences().AddReference(asset_path)
    setTranslate(obstaclePrim, location)


def CreateBackground(stage, background_stage):
    background_path = "/background"
    if not stage.GetPrimAtPath(background_path):
        backPrim = stage.DefinePrim(background_path, "Xform")
        backPrim.GetReferences().AddReference(background_stage)
        setTranslate(backPrim, Gf.Vec3d(5747.25, 1826.020, -117.200))
        setRotate(backPrim, Gf.Matrix3d(Gf.Rotation(Gf.Vec3d(0, 0, 1), 90)))


def SetupPhysics(stage):
    metersPerUnit = UsdGeom.GetStageMetersPerUnit(stage)
    gravityScale = 9.81 / metersPerUnit
    gravity = Gf.Vec3f(0.0, 0.0, -gravityScale)
    scene = PhysicsSchema.PhysicsScene.Define(stage, "/physics/scene")
    scene.CreateGravityAttr().Set(gravity)

    PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath("/physics/scene"))
    physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(stage, "/physics/scene")
    physxSceneAPI.CreatePhysxSceneEnableCCDAttr(True)
    physxSceneAPI.CreatePhysxSceneEnableStabilizationAttr(True)
    physxSceneAPI.CreatePhysxSceneEnableGPUDynamicsAttr(False)
    physxSceneAPI.CreatePhysxSceneBroadphaseTypeAttr("MBP")
    physxSceneAPI.CreatePhysxSceneSolverTypeAttr("TGS")


class Scenario:
    """ Defines a block stacking scenario

    Scenarios define the life cycle within kit and handle init, startup, shutdown etc. 
    """

    def __init__(self, editor, dc, mp):
        self._editor = editor
        self._stage = omni.usd.get_context().get_stage()
        self._dc = dc
        self._mp = mp
        self._domains = []  # Contains instances of environment
        self._obstacles = []  # Containts references to any obstacles in the scenario
        self._executor = None
        self._created = False

        self.asset_path = "omni:/Projects/gtc_sj_2020"
        # use local content if not connected to omni server
        if len(omni.kit.connectionhub.get_connection_hub_interface().get_connection_handles()) <= 0:
            print("Use local content")
            self.asset_path = "art_assets/gtc_sj_2020"
        else:
            print("Use server content")

        self.ur10_table_usd = self.asset_path + "/Stage/StageD6SRT.usd"
        self.normal_klt_usd = self.asset_path + "/props/NormalKLT.usd"
        self.small_klt_usd = self.asset_path + "/props/SmallKLT.usd"
        self.small_tray_scale = np.array([0.19, 0.296, 0.08])
        self.background_usd = self.asset_path + "/Backgrounds/Warehouse/Warehouse_Empty_small.usd"
        self.rubiks_cube_usd = self.asset_path + "/props/Rubiks_Cube/Rubiks_Cube.usd"

    def __del__(self):
        self.robot_created = False
        if self._executor:
            self._executor.shutdown(True)
            self._executor = None
        self._domains = []
        gc.collect()

    def reset_blocks(self, *args):
        pass

    def stop_tasks(self, *args):
        pass

    def pause_tasks(self, *args):
        return True

    def step(self, step):
        pass

    def open_gripper(self):
        pass

    def add_tray(self, *args):
        pass

    def create_UR10(self, *args):
        self._created = True
        self._stage = omni.usd.get_context().get_stage()
        setUpZAxis(self._stage)
        self.stop_tasks()
        pass

    def register_assets(self, *args):
        pass

    def task(self, domain):
        pass

    def perform_tasks(self, *args):
        return False

    def is_created(self):
        return self._created
