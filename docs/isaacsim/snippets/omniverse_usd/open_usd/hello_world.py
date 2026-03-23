# -- Test setup --
from pxr import Usd, UsdGeom

stage = Usd.Stage.CreateInMemory()
# -- End test setup --
xformPrim = UsdGeom.Xform.Define(stage, "/hello")
spherePrim = UsdGeom.Sphere.Define(stage, "/hello/world")
# stage.GetRootLayer().SaveAs('/path/to/hello_world.usda')
print(stage.GetRootLayer().ExportToString())
