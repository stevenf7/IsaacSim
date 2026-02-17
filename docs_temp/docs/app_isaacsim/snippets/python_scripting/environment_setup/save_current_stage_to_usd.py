import carb
import omni

# Create a prim
result, path = omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Cube")
# Change the path as needed
omni.usd.get_context().save_as_stage("/path/to/asset/saved.usd", None)
