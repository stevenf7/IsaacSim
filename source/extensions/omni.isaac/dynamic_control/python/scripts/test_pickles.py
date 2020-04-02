import carb
import pickle

from .. import _dynamic_control as dynamic_control


def test_pickles():
    print("Testing pickles")

    print("Float3:")
    f3_src = carb.Float3(2.0, -1.5, 13.37)
    f3_bytes = pickle.dumps(f3_src)
    f3_dst = pickle.loads(f3_bytes)
    print(f3_src)
    print(f3_dst)

    print("Float4:")
    f4_src = carb.Float4(2.0, -1.5, 13.37, 42)
    f4_bytes = pickle.dumps(f4_src)
    f4_dst = pickle.loads(f4_bytes)
    print(f4_src)
    print(f4_dst)

    print("Transform:")
    tx_src = dynamic_control.Transform((0.5, 1.25, -1.0), (0.1, 0.2, 0.3, 0.4))
    tx_bytes = pickle.dumps(tx_src)
    tx_dst = pickle.loads(tx_bytes)
    print(tx_src.p, tx_src.r)
    print(tx_dst.p, tx_dst.r)

    print("Velocity:")
    vel_src = dynamic_control.Velocity((-1.1, -2.2, -3.3), (17, 42, 33))
    vel_bytes = pickle.dumps(vel_src)
    vel_dst = pickle.loads(vel_bytes)
    print(vel_src.linear, vel_src.angular)
    print(vel_dst.linear, vel_dst.angular)

    print("RigidBodyState:")
    rbs_src = dynamic_control.RigidBodyState()
    rbs_src.pose = tx_src
    rbs_src.vel = vel_src
    rbs_bytes = pickle.dumps(rbs_src)
    rbs_dst = pickle.loads(rbs_bytes)
    print(rbs_src.pose.p, rbs_src.pose.r, rbs_src.vel.linear, rbs_src.vel.angular)
    print(rbs_dst.pose.p, rbs_dst.pose.r, rbs_dst.vel.linear, rbs_dst.vel.angular)

    print("DofState:")
    ds_src = dynamic_control.DofState(2.0, -1.5)
    ds_bytes = pickle.dumps(ds_src)
    ds_dst = pickle.loads(ds_bytes)
    print(ds_src.pos, ds_src.vel)
    print(ds_dst.pos, ds_dst.vel)

    print("DofProperties:")
    dp_src = dynamic_control.DofProperties()
    dp_src.type = dynamic_control.DOF_ROTATION
    dp_src.has_limits = True
    dp_src.lower = -3.14
    dp_src.upper = 1.57
    dp_src.drive_mode = dynamic_control.DRIVE_POS
    dp_src.max_velocity = 123.4
    dp_src.max_effort = 1234.5
    dp_src.stiffness = 1e4
    dp_src.damping = 1e3
    dp_bytes = pickle.dumps(dp_src)
    dp_dst = pickle.loads(dp_bytes)
    print(
        dp_src.type,
        dp_src.has_limits,
        dp_src.lower,
        dp_src.upper,
        dp_src.drive_mode,
        dp_src.max_velocity,
        dp_src.max_effort,
        dp_src.stiffness,
        dp_src.damping,
    )
    print(
        dp_dst.type,
        dp_dst.has_limits,
        dp_dst.lower,
        dp_dst.upper,
        dp_dst.drive_mode,
        dp_dst.max_velocity,
        dp_dst.max_effort,
        dp_dst.stiffness,
        dp_dst.damping,
    )

    print("AttractorProperties:")
    ap_src = dynamic_control.AttractorProperties()
    ap_src.body = 123456789
    ap_src.axes = dynamic_control.AXIS_ALL
    ap_src.target.p = (-1, -2, -3)
    ap_src.target.r = (1, 2, 3, 4)
    ap_src.offset.p = (-0.1, -0.2, -0.3)
    ap_src.offset.r = (0.1, 0.2, 0.3, 0.4)
    ap_src.stiffness = 1e5
    ap_src.damping = 1e4
    ap_src.force_limit = 1e3
    ap_bytes = pickle.dumps(ap_src)
    ap_dst = pickle.loads(ap_bytes)
    print(
        ap_src.body,
        ap_src.axes,
        ap_src.target.p,
        ap_src.target.r,
        ap_src.offset.p,
        ap_src.offset.r,
        ap_src.stiffness,
        ap_src.damping,
        ap_src.force_limit,
    )
    print(
        ap_dst.body,
        ap_dst.axes,
        ap_dst.target.p,
        ap_dst.target.r,
        ap_dst.offset.p,
        ap_dst.offset.r,
        ap_dst.stiffness,
        ap_dst.damping,
        ap_dst.force_limit,
    )
