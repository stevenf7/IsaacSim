from isaacsim import SimulationApp

# Start the application
simulation_app = SimulationApp({"headless": False})

# Get the utility to enable extensions
from isaacsim.core.utils.extensions import enable_extension

# Enable the layers and stage windows in the UI
enable_extension("omni.kit.widget.stage")
enable_extension("omni.kit.widget.layers")

simulation_app.update()
