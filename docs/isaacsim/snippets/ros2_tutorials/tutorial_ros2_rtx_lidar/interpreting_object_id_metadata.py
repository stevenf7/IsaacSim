import json

import numpy as np
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py.point_cloud2 import read_points
from std_msgs.msg import String


class ROS2ObjectIDSubscriber(Node):
    def __init__(self):

        super().__init__("ros2_object_id_subscriber")

        self.point_cloud2_subscriber = self.create_subscription(
            PointCloud2, "point_cloud", self.point_cloud2_callback, 10
        )
        self.object_id_map_subscriber = self.create_subscription(
            String, "object_id_map", self.object_id_map_callback, 10
        )
        self.object_id_map = None

    def point_cloud2_callback(self, msg: PointCloud2):
        self.get_logger().info(f"Received point cloud.")
        points = read_points(
            msg, field_names=("x", "y", "z", "object_id_0", "object_id_1", "object_id_2", "object_id_3"), skip_nans=True
        )
        if self.object_id_map is None:
            return
        object_ids_as_uint32 = (
            np.stack(
                [
                    points["object_id_0"],
                    points["object_id_1"],
                    points["object_id_2"],
                    points["object_id_3"],
                ],
                axis=1,
            )
            .flatten()
            .reshape(-1, 4)
        )
        object_ids_as_uint128 = [int.from_bytes(group.tobytes(), byteorder="little") for group in object_ids_as_uint32]
        prim_paths = [self.object_id_map[str(i)] for i in object_ids_as_uint128]
        print(prim_paths)

    def object_id_map_callback(self, msg: String):
        self.get_logger().info(f"Received object id map: {msg.data}")
        self.object_id_map = json.loads(msg.data)["id_to_labels"]
