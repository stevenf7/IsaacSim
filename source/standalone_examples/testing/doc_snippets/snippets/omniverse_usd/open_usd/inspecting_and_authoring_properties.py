from pxr import Usd, Vt

stage = Usd.Stage.Open("/path/to/HelloWorld.usda")
xform = stage.GetPrimAtPath("/hello")
sphere = stage.GetPrimAtPath("/hello/world")
print(xform.GetPropertyNames())
print(sphere.GetPropertyNames())
