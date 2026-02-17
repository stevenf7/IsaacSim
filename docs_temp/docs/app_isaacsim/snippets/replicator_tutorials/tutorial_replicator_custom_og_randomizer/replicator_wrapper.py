import omni.replicator.core as rep
from omni.replicator.core.scripts.utils import (
    ReplicatorItem,
    ReplicatorWrapper,
    create_node,
    set_target_prims,
)


@ReplicatorWrapper
def on_sphere(
    radius: float = 1.0,
    input_prims: ReplicatorItem | list[str] | None = None,
) -> ReplicatorItem:

    node = create_node("isaacsim.replicator.examples.OgnSampleOnSphere", radius=radius)
    if input_prims:
        set_target_prims(node, "inputs:prims", input_prims)
    return node


@ReplicatorWrapper
def in_sphere(
    radius: float = 1.0,
    input_prims: ReplicatorItem | list[str] | None = None,
) -> ReplicatorItem:

    node = create_node("isaacsim.replicator.examples.OgnSampleInSphere", radius=radius)
    if input_prims:
        set_target_prims(node, "inputs:prims", input_prims)
    return node


@ReplicatorWrapper
def between_spheres(
    radius1: float = 0.5,
    radius2: float = 1.0,
    input_prims: ReplicatorItem | list[str] | None = None,
) -> ReplicatorItem:

    node = create_node("isaacsim.replicator.examples.OgnSampleBetweenSpheres", radius1=radius1, radius2=radius2)
    if input_prims:
        set_target_prims(node, "inputs:prims", input_prims)
    return node


prim_count = 50
prim_scale = 0.1
rad_in = 0.5
rad_on = 1.5
rad_bet1 = 2.5
rad_bet2 = 3.5

# Create the default prims
sphere = rep.create.sphere(count=prim_count, scale=prim_scale)
cube = rep.create.cube(count=prim_count, scale=prim_scale)
cylinder = rep.create.cylinder(count=prim_count, scale=prim_scale)

# Create the randomization graph
with rep.trigger.on_frame():
    with sphere:
        rep.randomizer.rotation()
        in_sphere(rad_in)

    with cube:
        rep.randomizer.rotation()
        on_sphere(rad_on)

    with cylinder:
        rep.randomizer.rotation()
        between_spheres(rad_bet1, rad_bet2)
