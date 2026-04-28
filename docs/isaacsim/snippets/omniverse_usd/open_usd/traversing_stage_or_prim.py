# -- Test setup --
import omni.usd
from pxr import UsdGeom

stage = omni.usd.get_context().get_stage()
UsdGeom.Xform.Define(stage, "/World")
stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))


def do_something(prim):
    pass


# -- End test setup --
# For stage traversal there's a built-in method:
for a in stage.Traverse():
    do_something(a)

# For prim, it's not the same method though
from pxr import Usd

prim = stage.GetDefaultPrim()
for a in Usd.PrimRange(prim):
    do_something(a)
