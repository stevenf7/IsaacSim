local ext = get_current_extension_info()
ext.target_dir = deprecated_exts_path.."/"..ext.id

project_ext (ext)

repo_build.prebuild_link {
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}

repo_build.prebuild_link {
    {"python/scripts/world", ext.target_dir.."/omni/isaac/core/world"},
    {"python/scripts/simulation_context", ext.target_dir.."/omni/isaac/core/simulation_context"},
    {"python/scripts/utils", ext.target_dir.."/omni/isaac/core/utils"},
    {"python/scripts/prims", ext.target_dir.."/omni/isaac/core/prims"},
    {"python/scripts/scenes", ext.target_dir.."/omni/isaac/core/scenes"},
    {"python/scripts/objects", ext.target_dir.."/omni/isaac/core/objects"},
    {"python/scripts/physics_context", ext.target_dir.."/omni/isaac/core/physics_context"},
    {"python/scripts/articulations", ext.target_dir.."/omni/isaac/core/articulations"},
    {"python/scripts/controllers", ext.target_dir.."/omni/isaac/core/controllers"},
    {"python/scripts/loggers", ext.target_dir.."/omni/isaac/core/loggers"},
    {"python/scripts/materials", ext.target_dir.."/omni/isaac/core/materials"},
    {"python/scripts/robots", ext.target_dir.."/omni/isaac/core/robots"},
    {"python/scripts/tasks", ext.target_dir.."/omni/isaac/core/tasks"}}


repo_build.prebuild_copy {
        { "python/scripts/*.py", ext.target_dir.."/omni/isaac/core" }}

