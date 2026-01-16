from pxr import Usd, UsdGeom

stage = Usd.Stage.CreateNew("/path/to/HelloWorld.usda")
xformPrim = UsdGeom.Xform.Define(stage, "/hello")
spherePrim = UsdGeom.Sphere.Define(stage, "/hello/world")
# generic_spherePrim = stage.DefinePrim('/hello/world_generic', 'Sphere')
stage.GetRootLayer().Save()
