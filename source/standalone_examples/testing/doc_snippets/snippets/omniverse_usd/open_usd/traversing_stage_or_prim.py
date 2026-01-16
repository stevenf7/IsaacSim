# For stage traversal there's a built-in method:
for a in stage.Traverse():
    do_something(a)

# For prim, it's not the same method though
from pxr import Usd

prim = stage.GetDefaultPrim()
for a in Usd.PrimRange(prim):
    do_something(a)
