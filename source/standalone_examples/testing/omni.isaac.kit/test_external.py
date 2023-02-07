import sys
import numpy as np
from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp()

import omni
from omni.isaac.core.utils.extensions import enable_extension, disable_extension

simulation_app.update()

enable_extension("semantics.schema.editor")
simulation_app.update()
disable_extension("semantics.schema.editor")
simulation_app.update()
enable_extension("omni.cuopt.examples")
simulation_app.update()
disable_extension("omni.cuopt.examples")
simulation_app.update()
enable_extension("omni.anim.people")
simulation_app.update()
disable_extension("omni.anim.people")
simulation_app.update()
# Cleanup application
simulation_app.close()
