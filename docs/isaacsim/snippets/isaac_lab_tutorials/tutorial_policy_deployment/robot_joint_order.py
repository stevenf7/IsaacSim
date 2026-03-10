from isaacsim.core.experimental.prims import Articulation

# Open your USD and PLAY the simulation before running this snippet
prim = Articulation(paths="<your_robot_prim_path>")
print(str(prim.dof_names))
