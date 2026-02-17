from isaacsim.core.prims import SingleArticulation

prim_path = "/h1"
prim = SingleArticulation(prim_path=prim_path, name="h1")
print(prim.dof_names)
print(prim.dof_properties)
