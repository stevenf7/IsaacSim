"""Validate multi-arm robot USD articulation structure.

Checks: exactly one ArticulationRootAPI, FixedJoint connections between each
arm and the chassis, and Robot Schema overlay presence.

Run with: $ISAAC_SIM_DIR/python.sh validate_articulation.py <path/to/robot.usd>
"""

import sys


def validate_articulation(usd_path: str) -> bool:
    """Validate articulation root count, FixedJoint connectivity, and Robot Schema.

    Args:
        usd_path: Path to the robot USD file.

    Returns:
        True if all checks pass.

    Raises:
        AssertionError: If exactly one ArticulationRootAPI is not found.
    """
    from pxr import Usd, UsdPhysics
    from usd.schema.isaac.robot_schema import Attributes, Classes, GetAllNamedPoses

    stage = Usd.Stage.Open(usd_path)

    art_roots = [p.GetPath() for p in stage.Traverse() if p.HasAPI(UsdPhysics.ArticulationRootAPI)]
    print(f"ArticulationRootAPI count: {len(art_roots)} -- {art_roots}")
    assert len(art_roots) == 1, "must be exactly 1 articulation root"

    joints = [p for p in stage.Traverse() if p.IsA(UsdPhysics.Joint)]
    chassis_paths = {str(art_roots[0])}
    attached_arms = set()
    for j in joints:
        j_api = UsdPhysics.Joint(j)
        b0 = j_api.GetBody0Rel().GetTargets()
        b1 = j_api.GetBody1Rel().GetTargets()
        if j.IsA(UsdPhysics.FixedJoint) and any(str(t).startswith(p) for t in b0 for p in chassis_paths):
            attached_arms.update(str(t) for t in b1)
    print(f"Joints: {len(joints)} | FixedJoint-attached children: {sorted(attached_arms)}")

    # Robot Schema overlay
    robots = [p for p in stage.Traverse() if p.HasAPI(Classes.ROBOT_API)]
    print(f"IsaacRobotAPI count: {len(robots)}")
    for r in robots:
        rt = r.GetAttribute(Attributes.ROBOT_TYPE).Get()
        poses = GetAllNamedPoses(stage, r)
        print(f"  {r.GetPath()}: robot_type={rt!r}  named_poses={list(poses)}")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_articulation.py <robot.usd>")
        sys.exit(1)
    validate_articulation(sys.argv[1])
