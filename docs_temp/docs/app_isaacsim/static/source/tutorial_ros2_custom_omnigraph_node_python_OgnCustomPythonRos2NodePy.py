import omni.graph.core
import rclpy
import std_msgs.msg
from custom.python.ros2_node.ogn.OgnCustomPythonRos2NodePyDatabase import OgnCustomPythonRos2NodePyDatabase
from isaacsim.core.nodes import BaseResetNode


class OgnCustomPythonRos2NodePyInternalState(BaseResetNode):
    """Convenience class for maintaining per-node state information.

    It inherits from ``BaseResetNode`` to do custom reset operation when the timeline is stopped."""

    def __init__(self):
        """Instantiate the per-node state information"""
        self._data = None
        self._ros2_node = None
        self._subscription = None
        # call parent class to set up timeline event for custom reset
        super().__init__(initialize=False)

    @property
    def data(self):
        """Get received data, and clean it after reading"""
        tmp = self._data
        self._data = None
        return tmp

    def _callback(self, msg):
        """Function that is called when a message is received by the subscription."""
        self._data = msg.data

    def initialize(self, node_name, topic_name):
        """Intitialize ROS 2 node and subscription."""
        try:
            rclpy.init()
        except:
            pass
        # create ROS 2 node
        if not self._ros2_node:
            self._ros2_node = rclpy.create_node(node_name=node_name)
        # create ROS 2 subscription
        if not self._subscription:
            self._subscription = self._ros2_node.create_subscription(
                msg_type=std_msgs.msg.Int32, topic=topic_name, callback=self._callback, qos_profile=10
            )
        self.initialized = True

    def spin_once(self, timeout_sec=0.01):
        """Do ROS 2 work to take an incoming message from the topic, if any."""
        rclpy.spin_once(self._ros2_node, timeout_sec=timeout_sec)

    def custom_reset(self):
        """On timeline stop, destroy ROS 2 subscription and node."""
        if self._ros2_node:
            self._ros2_node.destroy_subscription(self._subscription)
            self._ros2_node.destroy_node()

        self._data = None
        self._ros2_node = None
        self._subscription = None
        self.initialized = False

        rclpy.try_shutdown()


class OgnCustomPythonRos2NodePy:
    """The OmniGraph node class"""

    @staticmethod
    def fibonacci(n):
        """Compute the Fibonacci sequence value for the given number iteratively"""
        if n <= 0:
            return 0
        elif n == 1:
            return 1
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

    @staticmethod
    def internal_state():
        """Get per-node state information."""
        return OgnCustomPythonRos2NodePyInternalState()

    @staticmethod
    def compute(db) -> bool:
        """Compute the output based on inputs and internal state."""
        state = db.per_instance_state

        try:
            # check if state (ROS 2 node and subscriber is initialized)
            if not state.initialized:
                state.initialize(node_name="custom_python_ros2_node", topic_name=db.inputs.topic)
            # spin state to take incoming messages
            state.spin_once()

            # cache incomming data
            number = state.data
            if number is not None:
                # compute the Fibonacci sequence value for the given number
                value = OgnCustomPythonRos2NodePy.fibonacci(number)
                # check for uint64 overflow
                if value > 2**64:
                    db.log_warn(f"Fibonacci number {number} exceeds uint64's storage capacity")
                    return False
                # output value and trigger output execution
                db.outputs.fibonacci = value
                db.outputs.execOut = omni.graph.core.ExecutionAttributeState.ENABLED
        except Exception as e:
            db.log_error(f"Computation error: {e}")
            return False
        return True

    @staticmethod
    def release(node):
        """Release per-node state information."""
        try:
            state = OgnCustomPythonRos2NodePyDatabase.per_instance_internal_state(node)
        except Exception as e:
            return
        # reset state
        state.reset()
        state.initialized = False
