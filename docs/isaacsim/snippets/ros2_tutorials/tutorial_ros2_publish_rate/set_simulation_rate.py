from isaacsim.core.rendering_manager import RenderingManager
from isaacsim.core.simulation_manager import SimulationManager

# Set physics, timeline, and run-loop rates coherently before pressing Play.
# Assumes `/app/runLoops/main/rateLimitEnabled` is true (default in the full
# Isaac Sim GUI app; false in `isaacsim.exp.base.kit` / standalone Python). If
# it is false, set it to True first or the loop will tick unthrottled. See the
# `RenderingManager.set_dt` docstring for the full effect list.
target_hz = 60
SimulationManager.setup_simulation(dt=1.0 / target_hz)
RenderingManager.set_dt(1.0 / target_hz)
