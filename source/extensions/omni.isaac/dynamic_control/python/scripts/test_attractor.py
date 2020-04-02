import numpy as np
import carb

from .. import _dynamic_control


class TestAttractor:
    def start(self, dc):
        print("Starting bouncy")

        ar_path = "/panda"
        print("Registering articulation '%s'" % ar_path)

        ar = dc.get_articulation(ar_path)
        if ar == _dynamic_control.INVALID_HANDLE:
            raise Exception("Failed to get articulation at '%s'" % ar_path)

        # put drives in velocity control mode to dampen motion
        dof_props = dc.get_articulation_dof_properties(ar)
        print(dof_props)
        dof_props["driveMode"].fill(_dynamic_control.DRIVE_VEL)
        dof_props["stiffness"].fill(0.0)
        dof_props["damping"].fill(5.0)
        dc.set_articulation_dof_properties(ar, dof_props)
        # print(dc.get_articulation_dof_properties(ar))

        # set velocity targets
        num_dofs = dc.get_articulation_dof_count(ar)
        vel_targets = np.zeros(num_dofs, dtype=np.float32)
        dc.set_articulation_dof_velocity_targets(ar, vel_targets)

        # get "hand" link
        hand = dc.find_articulation_body(ar, "panda_link7")
        hand_pose = dc.get_rigid_body_pose(hand)
        print("Hand pose:", hand_pose.p, hand_pose.r)

        # create attractor
        att_props = _dynamic_control.AttractorProperties()
        att_props.axes = _dynamic_control.AXIS_ALL
        att_props.body = hand
        att_props.target.p.x = hand_pose.p.x  # + 10
        att_props.target.p.y = hand_pose.p.y
        att_props.target.p.z = hand_pose.p.z
        att_props.target.r = hand_pose.r
        att_props.stiffness = 1e6
        att_props.damping = 1e3

        attractor = dc.create_rigid_body_attractor(att_props)

        self.ar = ar

        self.att = attractor
        self.att_props = att_props
        self.att_pos = hand_pose.p.y
        self.att_min = hand_pose.p.y - 15
        self.att_max = hand_pose.p.y + 15
        self.att_speed = 20

    def stop(self, dc):
        dc.destroy_rigid_body_attractor(self.att)

    def update(self, dc, dt):

        if self.att_speed > 0 and self.att_pos > self.att_max:
            self.att_speed = -self.att_speed
        elif self.att_speed < 0 and self.att_pos < self.att_min:
            self.att_speed = -self.att_speed

        self.att_pos += dt * self.att_speed
        print(self.att_pos)

        self.att_props.target.p.y = self.att_pos

        dc.set_attractor_target(self.att, self.att_props.target)

        # dc.update_context(self.ctx)


def get_test_attractor():
    return TestAttractor()
