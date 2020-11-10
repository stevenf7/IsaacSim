local ext = get_current_extension_info()
project_ext (ext)
    

-- repo_build.prebuild_link {
--     { ext_source.."/config", ext_folder.."/config" },
--     { ext_source.."/python/scripts", ext_folder.."/omni/isaac/exploded_view/scripts" },
-- }

-- repo_build.prebuild_copy {
--     { ext_source.."/python/*.py", ext_folder.."/omni/isaac/exploded_view" },
-- }

-- -- project "omni.isaac.exploded_view"
-- -- kind "None"
-- -- --add_impl_folder("")

-- -- vpaths { ["*"] = ext_folder }
-- -- files { ext_folder.."/**.py" }
-- -- files { ext_folder.."/**.toml" }