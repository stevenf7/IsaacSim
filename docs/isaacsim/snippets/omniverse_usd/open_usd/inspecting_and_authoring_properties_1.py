# -- Test setup --
from pxr import Usd, UsdGeom

stage = Usd.Stage.CreateInMemory()
UsdGeom.Sphere.Define(stage, "/hello/world")
sphere = stage.GetPrimAtPath("/hello/world")
# -- End test setup --

radiusAttr = sphere.GetAttribute("radius")
print(radiusAttr.Get())
radiusAttr.Set(0.50)
print(radiusAttr.Get())
