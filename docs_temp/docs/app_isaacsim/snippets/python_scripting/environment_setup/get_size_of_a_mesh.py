import omni
from pxr import Gf, Usd, UsdGeom

stage = omni.usd.get_context().get_stage()
result, path = omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Cone")
# Get the prim
prim = stage.GetPrimAtPath(path)
# Get the size
bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), includedPurposes=[UsdGeom.Tokens.default_])
bbox_cache.Clear()
prim_bbox = bbox_cache.ComputeWorldBound(prim)
prim_range = prim_bbox.ComputeAlignedRange()
prim_size = prim_range.GetSize()
print(prim_size)
