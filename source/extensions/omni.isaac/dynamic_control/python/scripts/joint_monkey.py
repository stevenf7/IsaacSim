import numpy as np

from .. import _dynamic_control

# joint animation states
ANIM_SEEK_LOWER = 1
ANIM_SEEK_UPPER = 2
ANIM_SEEK_DEFAULT = 3
ANIM_FINISHED = 4


def clamp(x, min_value, max_value):
    return max(min(x, max_value), min_value)


class JointMonkey:
    def start(self, dc):
        print("Starting joint monkey")

        ar_path = "/panda"
        print("Registering articulation '%s'" % ar_path)

        ar = dc.get_articulation(ar_path)
        print("Got ar", ar)
        if ar == _dynamic_control.INVALID_HANDLE:
            return False

        num_dofs = dc.get_articulation_dof_count(ar)
        dof_props = dc.get_articulation_dof_properties(ar)
        print(dof_props)

        dof_types = dof_props["type"]
        has_limits = dof_props["hasLimits"]
        lower_limits = dof_props["lower"]
        upper_limits = dof_props["upper"]

        # disable any drives
        dof_props["driveMode"].fill(_dynamic_control.DRIVE_NONE)
        dof_props["stiffness"].fill(0.0)
        dof_props["damping"].fill(0.0)
        dc.set_articulation_dof_properties(ar, dof_props)

        # allocate dof state buffer
        dof_states = np.zeros(num_dofs, dtype=_dynamic_control.DofState.dtype)
        print(dof_states)

        dof_positions = dof_states["pos"]

        speed_scale = 1.0

        # initialize default positions, limits, and speeds (make sure they are in reasonable ranges)
        defaults = np.zeros(num_dofs)
        speeds = np.zeros(num_dofs)
        for i in range(num_dofs):
            if has_limits[i]:
                if dof_types[i] == _dynamic_control.DOF_ROTATION:
                    lower_limits[i] = clamp(lower_limits[i], -math.pi, math.pi)
                    upper_limits[i] = clamp(upper_limits[i], -math.pi, math.pi)
                # make sure our default position is in range
                if lower_limits[i] > 0.0:
                    defaults[i] = lower_limits[i]
                elif upper_limits[i] < 0.0:
                    defaults[i] = upper_limits[i]
            else:
                # set reasonable animation limits for unlimited joints
                if dof_types[i] == _dynamic_control.DOF_ROTATION:
                    # unlimited revolute joint
                    lower_limits[i] = -math.pi
                    upper_limits[i] = math.pi
                elif dof_types[i] == _dynamic_control.DOF_TRANSLATION:
                    # unlimited prismatic joint
                    lower_limits[i] = -1.0
                    upper_limits[i] = 1.0
            # set DOF position to default
            dof_positions[i] = defaults[i]
            # set speed depending on DOF type and range of motion
            if dof_types[i] == _dynamic_control.DOF_ROTATION:
                speeds[i] = speed_scale * clamp(2 * (upper_limits[i] - lower_limits[i]), 0.25 * math.pi, 3.0 * math.pi)
            else:
                speeds[i] = speed_scale * clamp(2 * (upper_limits[i] - lower_limits[i]), 0.1, 7.0)

        print("Speeds:", speeds)

        self.ar = ar

        self.num_dofs = num_dofs
        self.defaults = defaults
        self.speeds = speeds
        self.lower_limits = lower_limits
        self.upper_limits = upper_limits

        self.dof_states = dof_states
        self.dof_positions = dof_positions

        self.anim_state = ANIM_SEEK_LOWER
        self.current_dof = 0

        self.counter = 0

        print("Animating DOF %d" % (self.current_dof,))
        # print("Animating DOF %d ('%s')" % (self.current_dof, dof_names[self.current_dof]))

        return True

    def update(self, dc, dt):
        # print("dt = %f" % dt)

        """        
        if True:
            # just hold
            dc.set_articulation_dof_states(self.ar, self.dof_states, _dynamic_control.STATE_POS)
            return
        """

        """
        if True:
            self.counter += 1
            if self.counter < 60:
                # just hold
                dc.set_articulation_dof_states(self.ar, self.dof_states, _dynamic_control.STATE_POS)
                return
            self.counter = 0
        """

        dof = self.current_dof
        speed = self.speeds[dof]

        # print("%f (%f, %f), %f" % (self.dof_positions[dof], self.lower_limits[dof], self.upper_limits[dof], speed))

        # animate the dofs
        if self.anim_state == ANIM_SEEK_LOWER:
            self.dof_positions[dof] -= speed * dt
            if self.dof_positions[dof] <= self.lower_limits[dof]:
                self.dof_positions[dof] = self.lower_limits[dof]
                self.anim_state = ANIM_SEEK_UPPER
        elif self.anim_state == ANIM_SEEK_UPPER:
            self.dof_positions[dof] += speed * dt
            if self.dof_positions[dof] >= self.upper_limits[dof]:
                self.dof_positions[dof] = self.upper_limits[dof]
                self.anim_state = ANIM_SEEK_DEFAULT
        if self.anim_state == ANIM_SEEK_DEFAULT:
            self.dof_positions[dof] -= speed * dt
            if self.dof_positions[dof] <= self.defaults[dof]:
                self.dof_positions[dof] = self.defaults[dof]
                self.anim_state = ANIM_FINISHED
        elif self.anim_state == ANIM_FINISHED:
            self.dof_positions[dof] = self.defaults[dof]
            self.current_dof = (dof + 1) % self.num_dofs
            self.anim_state = ANIM_SEEK_LOWER
            print("Animating DOF %d" % (self.current_dof,))
            # print("Animating DOF %d ('%s')" % (self.current_dof, dof_names[self.current_dof]))

        dc.set_articulation_dof_states(self.ar, self.dof_states, _dynamic_control.STATE_POS)

        # dof_states = dc.get_articulation_dof_states(self.ar, _dynamic_control.STATE_POS)
        # print(dof_states['pos'])

        # dc.update_context(self.ctx)


def get_joint_monkey():
    return JointMonkey()
