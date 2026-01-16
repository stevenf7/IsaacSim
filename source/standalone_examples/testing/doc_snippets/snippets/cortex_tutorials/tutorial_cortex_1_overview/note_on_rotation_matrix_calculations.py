import isaacsim.cortex.framework.math_util as math_util

R = robot.arm.get_fk_R()
ax, ay, az = math_util.unpack_R(R)
