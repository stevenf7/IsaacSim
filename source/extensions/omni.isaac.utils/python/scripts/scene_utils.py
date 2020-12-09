from pxr import Usd, UsdGeom, Gf, PhysxSchema, UsdPhysics


def set_up_z_axis(stage):
    rootLayer = stage.GetRootLayer()
    rootLayer.SetPermissionToEdit(True)
    with Usd.EditContext(stage, rootLayer):
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)


# Set default physics parameters
def setup_physics(stage):
    # Specify gravity
    metersPerUnit = UsdGeom.GetStageMetersPerUnit(stage)
    gravityScale = 9.81 / metersPerUnit
    scene = UsdPhysics.Scene.Define(stage, "/physics/scene")
    scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
    scene.CreateGravityMagnitudeAttr().Set(gravityScale)

    PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath("/physics/scene"))
    physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(stage, "/physics/scene")
    physxSceneAPI.CreateEnableCCDAttr(True)
    physxSceneAPI.CreateEnableStabilizationAttr(True)
    physxSceneAPI.CreateEnableGPUDynamicsAttr(False)
    physxSceneAPI.CreateBroadphaseTypeAttr("MBP")
    physxSceneAPI.CreateSolverTypeAttr("TGS")


# Specify position of a given prim, reuse any existing transform ops when possible
def set_translate(prim, new_loc):
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


# Create background stage
def create_background(stage, background_stage, background_path="/background", offset=Gf.Vec3d(0, 0, -104)):
    if not stage.GetPrimAtPath(background_path):
        backPrim = stage.DefinePrim(background_path, "Xform")
        backPrim.GetReferences().AddReference(background_stage)
        # Move the stage down -104cm so that the floor is below the table wheels
        set_translate(backPrim, offset)
