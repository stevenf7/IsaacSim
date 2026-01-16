# Pull assets towards the working area center by applying a random velocity towards the given target
def apply_velocities_towards_target(assets, target=(0, 0, 0)):
    for prim in assets:
        loc = prim.GetAttribute("xformOp:translate").Get()
        strength = random.uniform(0.1, 1.0)
        pull_vel = ((target[0] - loc[0]) * strength, (target[1] - loc[1]) * strength, (target[2] - loc[2]) * strength)
        prim.GetAttribute("physics:velocity").Set(pull_vel)
