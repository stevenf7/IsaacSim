from isaacsim.core.experimental.prims import Articulation

# Open your USD and PLAY the simulation before running this snippet
prim = Articulation(prim_paths_expr="<your_robot_prim_path>")
prim.initialize()
print(str(prim.dof_names))
