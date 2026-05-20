import tempfile
from pathlib import Path

import omni
from isaacsim.core.experimental.objects import Cube

# Create a prim
Cube("/World/Cube")
# Change the path as needed.
output_path = Path(tempfile.gettempdir()) / "isaacsim_saved_stage.usd"
omni.usd.get_context().save_as_stage(str(output_path), None)
print(f"Saved stage to {output_path}")
