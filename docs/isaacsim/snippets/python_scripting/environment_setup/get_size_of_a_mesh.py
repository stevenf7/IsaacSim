import isaacsim.core.experimental.utils.bounds as bounds_utils
from isaacsim.core.experimental.objects import Cone

cone = Cone("/World/Cone")
# Get the size
aabb = bounds_utils.compute_aabb(cone.paths[0])
prim_size = aabb[3:] - aabb[:3]
print(prim_size)
