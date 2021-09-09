import copy
from omni.isaac.dynamic_control import _dynamic_control
import carb
from sensor_msgs.msg import JointState
import numpy as np

# A simplified interface to a simulated franka panda robot
# will be refactored into a more concrete omni.isaac.franka extension in the future
class Panda:
    def __init__(self, stage=None, dc=None, usd_path=None, stage_path="/panda"):
        self._dc = dc
        self._state_flags = _dynamic_control.STATE_POS | _dynamic_control.STATE_VEL
        self.stage = stage
        self.articulation_handle = None
        self.usd_path = usd_path
        self.stage_path = stage_path
        self.prim = None

        self.prim = self.stage.DefinePrim(self.stage_path, "Xform")  # create an empty Xform at the given path
        self.prim.GetReferences().AddReference(self.usd_path)  # attach the USD to the given path
        self.dof_indices = []
        self.dof_handles = []

    def register(self):
        self.articulation_handle = self._dc.get_articulation(self.stage_path)
        for name in self.joint_names:
            self.dof_handles.append(self._dc.find_articulation_dof(self.articulation_handle, name))
            self.dof_indices.append(self._dc.find_articulation_dof_index(self.articulation_handle, name))

    @property
    def num_joints(self):
        return len(self.joint_names)

    @property
    def num_bodies(self):
        art = self.articulation_handle
        return self._dc.get_articulation_body_count(art)

    @property
    def joint_names(self):
        return [
            "panda_joint1",
            "panda_joint2",
            "panda_joint3",
            "panda_joint4",
            "panda_joint5",
            "panda_joint6",
            "panda_joint7",
        ]

    @property
    def joint_indices(self):
        return self.dof_indices

    @property
    def joint_handles(self):
        return self.dof_handles

    @property
    def joint_states(self):
        return copy.deepcopy(self._dc.get_articulation_dof_states(self.articulation_handle, self._state_flags))

    @joint_states.setter
    def joint_states(self, dof_states):
        self._dc.set_articulation_dof_states(self.articulation_handle, dof_states, self._state_flags)

    def disable_gravity(self, disabled=True):
        art = self.articulation_handle

        body_count = self._dc.get_articulation_body_count(art)
        for bodyIdx in range(body_count):
            body = self._dc.get_articulation_body(art, bodyIdx)
            self._dc.set_rigid_body_disable_gravity(body, disabled)

    def reset_to_target_pose(self):
        pass

    def set_position_targets(self, joint_positions):
        self._dc.set_articulation_dof_position_targets(self.articulation_handle, joint_positions.astype(np.float32))

    def get_position_targets(self):
        return self._dc.get_articulation_dof_position_targets(self.articulation_handle)

    def set_velocity_targets(self, joint_velocities):
        self._dc.set_articulation_dof_velocity_targets(self.articulation_handle, joint_velocities.astype(np.float32))

    def get_velocity_targets(self):
        return self._dc.get_articulation_dof_velocity_targets(self.articulation_handle)

    # switch between pos and vel modes
    def set_control_mode(self, position=False):
        props = self._dc.get_articulation_dof_properties(self.articulation_handle)
        num_dofs = self._dc.get_articulation_dof_count(self.articulation_handle)

        for i in range(num_dofs):
            if position:
                # untested values
                props["stiffness"][i] = 1e8
                props["damping"][i] = 1e5
            else:
                props["stiffness"][i] = 0
                props["damping"][i] = 1e10

        self._dc.set_articulation_dof_properties(self.articulation_handle, props)
        pass

    def get_joint_state_message(self):
        message = JointState()
        message.name = self.joint_names

        message.position = np.array([0.0] * self.num_joints)
        message.velocity = np.array([0.0] * self.num_joints)
        states = self.joint_states
        if states is None:
            carb.log_warn("Joint states is None...")
            return None

        for j in range(self.num_joints):
            index = self.joint_indices[j]
            message.position[j] = states["pos"][index]
            message.velocity[j] = states["vel"][index]
        return message
