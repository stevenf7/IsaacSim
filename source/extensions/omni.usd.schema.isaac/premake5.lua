local ext = get_current_extension_info()
project_ext (ext)

repo_build.prebuild_link 
{
    { "config", ext.target_dir.."/config" },
	{ "docs", ext.target_dir.."/docs"  },
    { "data", ext.target_dir.."/data" },
}
repo_build.prebuild_copy 
{
    { "python/__init__.py", ext.target_dir.."/usd/schema/isaac" },
}
repo_build.prebuild_copy 
{
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/share/usd/plugins/DrSchema", ext.target_dir.."/plugins/DrSchema" },
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/python/DrSchema/**", ext.target_dir.."/omni/isaac/DrSchema" },
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/${lib_prefix}drSchema${lib_ext}", ext.target_dir.."/bin"},
}
repo_build.prebuild_copy 
{
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/share/usd/plugins/RangeSensorSchema", ext.target_dir.."/plugins/RangeSensorSchema" },
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/python/RangeSensorSchema/**", ext.target_dir.."/omni/isaac/RangeSensorSchema" },
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/${lib_prefix}rangeSensorSchema${lib_ext}", ext.target_dir.."/bin"},
}
repo_build.prebuild_copy 
{
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/share/usd/plugins/IsaacSensorSchema", ext.target_dir.."/plugins/IsaacSensorSchema" },
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/python/IsaacSensorSchema/**", ext.target_dir.."/omni/isaac/IsaacSensorSchema" },
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/${lib_prefix}isaacSensorSchema${lib_ext}", ext.target_dir.."/bin"},
}
repo_build.prebuild_copy 
{
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/share/usd/plugins/RobotEngineBridgeSchema", ext.target_dir.."/plugins/RobotEngineBridgeSchema" },
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/python/RobotEngineBridgeSchema/**", ext.target_dir.."/omni/isaac/RobotEngineBridgeSchema" },
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/${lib_prefix}robotEngineBridgeSchema${lib_ext}", ext.target_dir.."/bin"},
}
repo_build.prebuild_copy 
{
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/share/usd/plugins/RosBridgeSchema", ext.target_dir.."/plugins/RosBridgeSchema" },
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/python/RosBridgeSchema/**", ext.target_dir.."/omni/isaac/RosBridgeSchema" },
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/${lib_prefix}rosBridgeSchema${lib_ext}", ext.target_dir.."/bin"},
}