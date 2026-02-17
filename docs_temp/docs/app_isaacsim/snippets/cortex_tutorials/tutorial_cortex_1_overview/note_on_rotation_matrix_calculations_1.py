import numpy as np

# Start with a z-axis pointing down. Project the end-effector's y-axis orthogonal to it (and
# normalize). Then construct the x-axis as the cross product.
target_az = np.array([0.0, 0.0, -1.0])
target_ay = math_util.normalized(math_util.proj_orth(ay, target_az))
target_ax = np.cross(target_ay, target_az)

# Pack the axes into the columns of a rotation matrix.
target_R = math_util.pack_R(target_ax, target_ay, target_az)
