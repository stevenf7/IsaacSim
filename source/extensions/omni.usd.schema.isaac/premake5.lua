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
    { "%{root}/schemas/_install/rangeSensorSchema/%{platform}_%{config}/usd/RangeSensorSchema", ext.target_dir.."/plugins/RangeSensorSchema" },
    { "%{root}/schemas/_install/rangeSensorSchema/%{platform}_%{config}/lib/python/RangeSensorSchema/**", ext.target_dir.."/omni/isaac/RangeSensorSchema" },
    { "%{root}/schemas/_install/rangeSensorSchema/%{platform}_%{config}/lib/${lib_prefix}rangeSensorSchema${lib_ext}", ext.target_dir.."/bin"},
}
repo_build.prebuild_copy 
{
    { "%{root}/schemas/_install/isaacSensorSchema/%{platform}_%{config}/usd/IsaacSensorSchema", ext.target_dir.."/plugins/IsaacSensorSchema" },
    { "%{root}/schemas/_install/isaacSensorSchema/%{platform}_%{config}/lib/python/IsaacSensorSchema/**", ext.target_dir.."/omni/isaac/IsaacSensorSchema" },
    { "%{root}/schemas/_install/isaacSensorSchema/%{platform}_%{config}/lib/${lib_prefix}isaacSensorSchema${lib_ext}", ext.target_dir.."/bin"},
}