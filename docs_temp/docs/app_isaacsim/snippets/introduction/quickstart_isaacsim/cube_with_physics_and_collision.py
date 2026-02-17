from isaacsim.core.experimental.materials import PreviewSurfaceMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim

cyan_material = PreviewSurfaceMaterial("/Materials/cyan")
cyan_material.set_input_values("diffuseColor", [0.0, 1.0, 1.0])

cube = Cube(
    paths="/dynamic_cube",
    positions=[0, -0.5, 1.5],
    sizes=0.3,
)
cube.apply_visual_materials(cyan_material)
RigidPrim(paths="/dynamic_cube")
GeomPrim(paths="/dynamic_cube", apply_collision_apis=True)
