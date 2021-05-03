local ext = get_current_extension_info()
project_ext (ext, { 
    define_test = false
})

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/ros2_bridge/scripts" },
    -- { "python/tests", ext.target_dir.."/omni/isaac/ros2_bridge/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}


repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/ros2_bridge" },
    { "rclpy/*.py", ext.target_dir.."/omni/isaac/rclpy" },
    { "%{root}/_build/target-deps/nv_ros2/lib/python3.7/site-packages", ext.target_dir.."/omni/isaac/rclpy" },
}
