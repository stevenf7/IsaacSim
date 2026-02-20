from isaacsim.core.experimental.prims import Articulation

articulation = Articulation("/Franka")
# Get articulation information
print("DOF count:", articulation.num_dofs)
print("DOF names:", articulation.dof_names)
print("DOF paths:", articulation.dof_paths)
print("DOF types:", articulation.dof_types)
print("Link count:", articulation.num_links)
print("Link names:", articulation.link_names)
print("Link paths:", articulation.link_paths)
