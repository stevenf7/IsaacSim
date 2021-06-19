# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from pxr import Usd, PhysxSchema
import omni


async def load_test_file(path_to_file: str):
    """
    Load the contents of the USD test file onto the stage, synchronously, when called as "await load_test_file(X)".
    In a testing environment we need to run one test at a time since there is no guarantee
    that tests can run concurrently, especially when loading files. This method encapsulates
    the logic necessary to load a test file using the open_stage_async method and then wait
    for it to complete before returning.
    :param test_file_name: Name of the test file to load - if not an absolute path then looks in the data/usd/tests/ComputeGraph directory
    :raises: ValueError if the test file is not a valid USD file
    """
    if not Usd.Stage.IsSupportedFile(path_to_file):
        raise ValueError("Only USD files can be loaded with this method")

    usd_context = omni.usd.get_context()
    usd_context.disable_save_to_recent_files()
    (result, error) = await omni.usd.get_context().open_stage_async(path_to_file)
    usd_context.enable_save_to_recent_files()
    return (result, error)


def set_scene_physics_type(gpu=False, scene_path="/physicsScene"):
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
