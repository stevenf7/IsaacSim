# Set the rt_subframes parameter for a specific capture step
rep.orchestrator.step(rt_subframes=4)

# Set the rt_subframes parameter globally
import carb.settings

carb.settings.get_settings().set("/omni/replicator/RTSubframes", 4)
