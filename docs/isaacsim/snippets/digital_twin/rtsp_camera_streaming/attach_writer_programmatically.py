import omni.kit.app
import omni.replicator.core as rep
import omni.usd
from pxr import UsdGeom

ext_mgr = omni.kit.app.get_app().get_extension_manager()
ext_mgr.set_extension_enabled_immediate("isaacsim.core.nodes", True)
ext_mgr.set_extension_enabled_immediate("isaacsim.streaming.rtsp", True)

from isaacsim.streaming.rtsp import RTSPStreamWriter
from isaacsim.streaming.rtsp.impl.render_var_utils import ensure_render_var_on_product

stage = omni.usd.get_context().get_stage()
UsdGeom.Camera.Define(stage, "/Camera")

render_product = rep.create.render_product("/Camera", (1280, 720))

success, _rv_path = ensure_render_var_on_product(stage, render_product.path, "LdrColor", "h264")
if not success:
    raise RuntimeError(f"Failed to create LdrColor render var on {render_product.path}")

writer = RTSPStreamWriter(
    port=8554,
    mountPath="/stream",
    encoding="h264",
    width=1280,
    height=720,
)
writer.attach([render_product])
