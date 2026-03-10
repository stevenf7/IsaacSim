from isaacsim.core.experimental.prims import Articulation

# Open your USD and PLAY the simulation before running this snippet
prim = Articulation(paths="<your_robot_prim_path>")
print("DOF names:", prim.dof_names)
print("DOF types:", prim.dof_types)
print("DOF limits:", prim.get_dof_limits())
print("DOF gains (stiffness, damping):", prim.get_dof_gains())
print("DOF max efforts:", prim.get_dof_max_efforts())
print("DOF max velocities:", prim.get_dof_max_velocities())
print("DOF drive types:", prim.get_dof_drive_types())
print("DOF friction:", prim.get_dof_friction_properties())
print("DOF armatures:", prim.get_dof_armatures())
