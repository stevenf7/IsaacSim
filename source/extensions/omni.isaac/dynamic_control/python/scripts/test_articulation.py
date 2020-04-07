import carb

from .. import _dynamic_control


def _print_body_rec(dc, body, indent_level=0):
    indent = " " * indent_level

    body_name = dc.get_rigid_body_name(body)
    print("%sBody: %s" % (indent, body_name))

    for i in range(dc.get_rigid_body_child_joint_count(body)):
        joint = dc.get_rigid_body_child_joint(body, i)
        joint_name = dc.get_joint_name(joint)
        child = dc.get_joint_child_body(joint)
        child_name = dc.get_rigid_body_name(child)
        print("%s  Joint: %s -> %s" % (indent, joint_name, child_name))

        _print_body_rec(dc, child, indent_level + 4)


def test_articulation(dc):

    ar_path = "/panda"
    ar = dc.get_articulation(ar_path)
    if ar == _dynamic_control.INVALID_HANDLE:
        print("*** Failed to get articulation at '%s'" % ar_path)
        return

    print("Got articulation handle", ar)

    print("--- Hierarchy")
    root = dc.get_articulation_root_body(ar)
    _print_body_rec(dc, root)

    print("--- Body states:")
    body_states = dc.get_articulation_body_states(ar, _dynamic_control.STATE_ALL)
    print(body_states)

    print("--- DOF states:")
    dof_states = dc.get_articulation_dof_states(ar, _dynamic_control.STATE_ALL)
    print(dof_states)

    print("--- DOF properties:")
    dof_props = dc.get_articulation_dof_properties(ar)
    print(dof_props)

    print("Done")
