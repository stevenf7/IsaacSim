# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# [snippet-start]
import omni.kit.actions.core
import omni.timeline
import omni.usd
from isaacsim.core.experimental.objects import Cube, Plane
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.core.simulation_manager.impl.mjc_scene import NewtonMjcScene
from pxr import Sdf, UsdGeom, UsdLux, UsdPhysics

omni.usd.get_context().new_stage()
SimulationManager.switch_physics_engine("newton")
stage = omni.usd.get_context().get_stage()

# Enable camera light and add distant light
action_registry = omni.kit.actions.core.get_action_registry()
action_registry.get_action("omni.kit.viewport.menubar.lighting", "set_lighting_mode_camera").execute()
UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight")).CreateIntensityAttr(500)

# Create physics scene
mjc_scene = NewtonMjcScene("/World/PhysicsScene")
mjc_scene.set_gravity((0.0, 0.0, -9.81))

# Create ground plane (collision + visual)
UsdGeom.Xform.Define(stage, "/World/GroundPlane")
Plane("/World/GroundPlane/CollisionPlane", axes="Z")
UsdPhysics.CollisionAPI.Apply(stage.GetPrimAtPath("/World/GroundPlane/CollisionPlane"))
visual_mesh = UsdGeom.Mesh.Define(stage, "/World/GroundPlane/VisualMesh")
size = 50.0
visual_mesh.CreatePointsAttr([(-size, -size, 0), (size, -size, 0), (size, size, 0), (-size, size, 0)])
visual_mesh.CreateFaceVertexCountsAttr([4])
visual_mesh.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
visual_mesh.CreateDisplayColorAttr([(0.5, 0.5, 0.5)])

# Create dynamic cube
Cube("/World/Cube", sizes=0.5, positions=[[0.0, 0.0, 2.0]])
cube_prim = stage.GetPrimAtPath("/World/Cube")
UsdPhysics.CollisionAPI.Apply(cube_prim)
UsdPhysics.RigidBodyAPI.Apply(cube_prim)

# Start simulation
timeline = omni.timeline.get_timeline_interface()
timeline.play()
