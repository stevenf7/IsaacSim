# -- Test setup --
import omni
from isaacsim.core.experimental.objects import Cube
from pxr import PhysxSchema

Cube(paths="/World/Cube", positions=[0, 0, 0.5])
# -- End test setup --

stage = omni.usd.get_context().get_stage()
parent_prim = stage.GetPrimAtPath("/World/Cube")
contact_report = PhysxSchema.PhysxContactReportAPI.Apply(parent_prim)
# Set a minimum threshold for the contact report to zero
contact_report.CreateThresholdAttr(0.0)
