from isaacsim.core.experimental.materials import OmniGlassMaterial
from isaacsim.core.experimental.objects import Cube

# Create a new material using OmniGlass.mdl
material = OmniGlassMaterial("/World/OmniGlassMaterial")
# Set material inputs, these can be determined by looking at the .mdl file
# or by selecting the Shader attached to the Material in the stage window and looking at the details panel
material.set_input_values("glass_color", [0.0, 1.0, 0.0])
material.set_input_values("glass_ior", [1.0])
# Create a prim to apply the material to
cube = Cube("/World/Cube")
# Bind the material to the prim
cube.apply_visual_materials(material)
