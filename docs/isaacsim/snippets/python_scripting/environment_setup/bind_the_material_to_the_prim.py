from isaacsim.core.experimental.materials import OmniPbrMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.storage.native import get_assets_root_path

texture_path = get_assets_root_path(skip_check=True) + "/Isaac/Samples/DR/Materials/Textures/marble_tile.png"

# Create a new material using OmniPBR.mdl
material = OmniPbrMaterial("/World/OmniPBRMaterial")
# Set material inputs, these can be determined by looking at the .mdl file
# or by selecting the Shader attached to the Material in the stage window and looking at the details panel
material.set_input_values("diffuse_texture", texture_path)
# Create a prim to apply the material to
cube = Cube("/World/Cube")
# Bind the material to the prim
cube.apply_visual_materials(material)
