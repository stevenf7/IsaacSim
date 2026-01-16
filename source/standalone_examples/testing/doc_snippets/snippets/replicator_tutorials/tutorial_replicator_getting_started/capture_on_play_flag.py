import omni.replicator.core as rep

rep.orchestrator.set_capture_on_play(False)
# OR
import carb.settings

carb.settings.get_settings().set("/omni/replicator/captureOnPlay", False)
