dst_folder = "exts/isaacsim.robot.schema/usd/plugins/robot_schema/resources"
repo_build.prebuild_copy
{
    { "generatedSchema.usda",  root.."/_build/%{cfg.system}-%{cfg.platform}/%{cfg.buildcfg}/"..dst_folder },
    -- { "schema.usda",  root.."/_build/%{cfg.system}-%{cfg.platform}/%{cfg.buildcfg}/"..dst_folder  },
    { "plugInfo.json",  root.."/_build/%{cfg.system}-%{cfg.platform}/%{cfg.buildcfg}/"..dst_folder  },
}
