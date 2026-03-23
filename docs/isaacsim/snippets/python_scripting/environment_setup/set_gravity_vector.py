# -- Test setup --
import omni.usd
from pxr import PhysxSchema, UsdPhysics

stage = omni.usd.get_context().get_stage()

# Create a physics scene
UsdPhysics.Scene.Define(stage, "/World/physicsScene")
# -- End test setup --

PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath("/World/physicsScene"))
physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(stage, "/World/physicsScene")
physxSceneAPI.CreateEnableCCDAttr(True)
physxSceneAPI.CreateEnableStabilizationAttr(True)
physxSceneAPI.CreateEnableGPUDynamicsAttr(False)
physxSceneAPI.CreateBroadphaseTypeAttr("MBP")
physxSceneAPI.CreateSolverTypeAttr("TGS")
