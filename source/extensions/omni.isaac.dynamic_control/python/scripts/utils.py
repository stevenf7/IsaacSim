# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


def set_scene_physics_type(gpu=False, scene_path="/physicsScene"):
    import omni
    from pxr import PhysxSchema

    stage = omni.usd.get_context().get_stage()

    physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(stage, scene_path)

    if physxSceneAPI.GetEnableCCDAttr().HasValue():
        physxSceneAPI.GetEnableCCDAttr().Set(True)
    else:
        physxSceneAPI.CreateEnableCCDAttr(True)

    if physxSceneAPI.GetEnableStabilizationAttr().HasValue():
        physxSceneAPI.GetEnableStabilizationAttr().Set(True)
    else:
        physxSceneAPI.CreateEnableStabilizationAttr(True)

    if physxSceneAPI.GetSolverTypeAttr().HasValue():
        physxSceneAPI.GetSolverTypeAttr().Set("TGS")
    else:
        physxSceneAPI.CreateSolverTypeAttr("TGS")

    if not physxSceneAPI.GetEnableGPUDynamicsAttr().HasValue():
        physxSceneAPI.CreateEnableGPUDynamicsAttr(False)

    if not physxSceneAPI.GetBroadphaseTypeAttr().HasValue():
        physxSceneAPI.CreateBroadphaseTypeAttr("MBP")

    if gpu:
        physxSceneAPI.GetEnableGPUDynamicsAttr().Set(True)
        physxSceneAPI.GetBroadphaseTypeAttr().Set("GPU")
    else:
        physxSceneAPI.GetEnableGPUDynamicsAttr().Set(False)
        physxSceneAPI.GetBroadphaseTypeAttr().Set("MBP")


def set_physics_frequency(frequency=60):
    import carb

    carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
    carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(frequency))
    carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(frequency))


async def simulate(seconds, dc=None, art=None, steps_per_sec=60):
    import omni

    for frame in range(int(steps_per_sec * seconds)):
        if art is not None and dc is not None:
            dc.wake_up_articulation(art)
        await omni.kit.app.get_app().next_update_async()


async def add_cube(stage, path, size, offset, physics=True, mass=0.0):
    import omni
    from pxr import UsdGeom, UsdPhysics

    cubeGeom = UsdGeom.Cube.Define(stage, path)
    cubePrim = stage.GetPrimAtPath(path)
    cubeGeom.CreateSizeAttr(size)
    cubeGeom.AddTranslateOp().Set(offset)
    await omni.kit.app.get_app().next_update_async()  # Need this to avoid flatcache errors
    if physics:
        rigid_api = UsdPhysics.RigidBodyAPI.Apply(cubePrim)
        rigid_api.CreateRigidBodyEnabledAttr(True)
        if mass > 0:
            massAPI = UsdPhysics.MassAPI.Apply(cubePrim)
            massAPI.CreateMassAttr(mass)
    UsdPhysics.CollisionAPI.Apply(cubePrim)
    await omni.kit.app.get_app().next_update_async()
    return cubePrim
