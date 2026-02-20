navigation_goal_node = Node(
    name="set_navigation_goal",
    package="isaac_ros_navigation_goal",
    executable="SetNavigationGoal",
    namespace="carter1",
    parameters=[
        {
            "map_yaml_path": map_yaml_file,
            "iteration_count": 3,
            "goal_generator_type": "RandomGoalGenerator",
            "action_server_name": "navigate_to_pose",
            "obstacle_search_distance_in_meters": 0.2,
            "goal_text_file_path": goal_text_file,
            "initial_pose": [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        }
    ],
    output="screen",
)
