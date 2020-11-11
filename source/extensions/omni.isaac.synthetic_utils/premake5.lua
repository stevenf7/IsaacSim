local ext = get_current_extension_info()
project_ext (ext)

-- -- Python code. Contains python sources, doesn't build or run, only for MSVS.
-- if os.target() == "windows" then
--     project "omni.isaac.synthetic_utils"
--         kind "None"
--         add_impl_folder("source/extensions/omni.isaac/synthetic_utils/python")
-- end

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/synthetic_utils/scripts" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/synthetic_utils" },
}
