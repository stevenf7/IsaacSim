# -- Test setup --
from pxr import Usd, UsdGeom, Vt

stage = Usd.Stage.CreateInMemory()
UsdGeom.Xform.Define(stage, "/hello")
UsdGeom.Sphere.Define(stage, "/hello/world")
# -- End test setup --
xform = stage.GetPrimAtPath("/hello")
sphere = stage.GetPrimAtPath("/hello/world")
print(xform.GetPropertyNames())
print(sphere.GetPropertyNames())
