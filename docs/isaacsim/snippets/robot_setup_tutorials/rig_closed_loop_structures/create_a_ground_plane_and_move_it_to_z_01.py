import omni.usd
from pxr import Gf, PhysicsSchemaTools, PhysxSchema, Sdf, Usd, UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()

# Create Xform nodes
xform = UsdGeom.Xform.Define(stage, "/World/Xform")
xform_1 = UsdGeom.Xform.Define(stage, "/World/Xform_1")

# Add Physics Rigid Body API to Xform nodes
for node in [xform, xform_1]:
    UsdPhysics.RigidBodyAPI.Apply(node.GetPrim())
    mass_api = UsdPhysics.MassAPI.Apply(node.GetPrim())
    mass_api.CreateMassAttr(0.1)

# Create Fixed Joint from Xform to Xform_1
fixed_joint = UsdPhysics.FixedJoint.Define(stage, xform.GetPath().AppendChild("fixed_joint"))
fixed_joint.CreateBody1Rel().SetTargets([str(xform.GetPath())])

# Create Prismatic Joints
prismatic_joint_1 = UsdPhysics.PrismaticJoint.Define(stage, "/World/Joint_Z")
prismatic_joint_1.CreateAxisAttr("Z")
prismatic_joint_1.CreateLowerLimitAttr(0.0)
prismatic_joint_1.CreateUpperLimitAttr(1.0)
prismatic_joint_1.CreateBody0Rel().SetTargets([str(xform.GetPath())])
prismatic_joint_1.CreateBody1Rel().SetTargets([str(xform_1.GetPath())])

prismatic_joint_2 = UsdPhysics.PrismaticJoint.Define(stage, "/World/Joint_X")
prismatic_joint_2.CreateAxisAttr("X")
prismatic_joint_2.CreateLowerLimitAttr(0.0)
prismatic_joint_2.CreateUpperLimitAttr(1.0)
prismatic_joint_2.CreateBody0Rel().SetTargets([str(xform_1.GetPath())])
prismatic_joint_2.CreateBody1Rel().SetTargets(
    ["/World/Robotiq_2F_85/base_link"]
)  # update this to match your robot's base_link prim path

# Add Prismatic Joint Drive with damping and stiffness
for joint in [prismatic_joint_1, prismatic_joint_2]:
    drive = UsdPhysics.DriveAPI.Apply(joint.GetPrim(), "linear")
    drive.CreateDampingAttr(10000)
    drive.CreateStiffnessAttr(10000)
    px_joint = PhysxSchema.PhysxJointAPI.Get(stage, str(joint.GetPath()))
    px_joint.CreateMaxJointVelocityAttr().Set(5.0)

# Add Ground Plane
PhysicsSchemaTools.addGroundPlane(stage, "/World/groundPlane", "Z", 100, Gf.Vec3f(0, 0, -0.1), Gf.Vec3f(1.0))

# Create cylinder mesh
result, path = omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Cylinder")
# Get the prim
cylinder_prim = stage.GetPrimAtPath(path)
cylinder_prim.GetAttribute("xformOp:scale").Set(
    (0.05, 0.05, 0.2)
)  # if your gripper is oriented differently, you may need to update the position and orientation of this cylinder or gripper accordingly to align them.  You can also do this post-creation.
cylinder_prim.GetAttribute("xformOp:translate").Set((0.12, 0, 0))

# Add Rigid Body and Mass API to cylinder
cylinder_body = UsdPhysics.RigidBodyAPI.Apply(cylinder_prim)
UsdPhysics.CollisionAPI.Apply(cylinder_prim)
mesh_collision = UsdPhysics.MeshCollisionAPI.Apply(cylinder_prim)
mesh_collision.CreateApproximationAttr().Set("convexHull")
massAPI = UsdPhysics.MassAPI.Apply(cylinder_body.GetPrim())
massAPI.CreateMassAttr(0.20)

# Create a Physics Scene
scene = UsdPhysics.Scene.Define(stage, Sdf.Path("/physicsScene"))
physxSceneAPI = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
# This is a Small test scene, no need for GPU Dynamics
physxSceneAPI.CreateEnableGPUDynamicsAttr(False)
