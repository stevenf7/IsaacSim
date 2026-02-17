import carb
import omni
import omni.physx
from omni.physx import get_physx_scene_query_interface
from pxr import Gf, UsdGeom, Vt


def report_hit(hit):
    # When a collision is detected, the object color changes to red.
    hitColor = Vt.Vec3fArray([Gf.Vec3f(180.0 / 255.0, 16.0 / 255.0, 0.0)])
    usdGeom = UsdGeom.Mesh.Get(omni.usd.get_context().get_stage(), hit.rigid_body)
    usdGeom.GetDisplayColorAttr().Set(hitColor)
    return True


def check_overlap():
    # Defines a cubic region to check overlap with
    extent = carb.Float3(20.0, 20.0, 20.0)
    origin = carb.Float3(0.0, 0.0, 0.0)
    rotation = carb.Float4(0.0, 0.0, 1.0, 0.0)
    # physX query to detect number of hits for a cubic region
    numHits = get_physx_scene_query_interface().overlap_box(extent, origin, rotation, report_hit, False)
    # physX query to detect number of hits for a spherical region
    # numHits = get_physx_scene_query_interface().overlap_sphere(radius, origin, report_hit, False)
    return numHits > 0
