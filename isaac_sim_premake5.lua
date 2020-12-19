
function include_physx()
    
    defines {  "PX_PHYSX_STATIC_LIB"}
    libdirs { "%{root}/_build/target-deps/nvtx/lib/x64" }

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}

    filter { "system:windows", "platforms:x86_64" }
        links { "nvToolsExt64_1"}
    filter { "system:linux", "platforms:x86_64" }
        links { "nvToolsExt"}
    filter {}

    filter { "system:windows", "platforms:x86_64", "configurations:debug" }
        libdirs { 
            "%{root}/_build/target-deps/physx/bin/win.x86_64.vc141.md/debug", 
        }
    filter { "system:windows", "platforms:x86_64", "configurations:release" }
        libdirs { 
            "%{root}/_build/target-deps/physx/bin/win.x86_64.vc141.md/checked",
        }
    filter {}

    filter { "system:linux", "platforms:x86_64","configurations:debug" }
        libdirs { 
            "%{root}/_build/target-deps/physx/bin/linux.clang/debug", 
        }
    filter { "system:linux", "platforms:x86_64","configurations:release" }
        libdirs { 
            "%{root}/_build/target-deps/physx/bin/linux.clang/checked", 
        }
    filter {}

    links { "PhysXExtensions_static_64", "PhysX_static_64", "PhysXPvdSDK_static_64","PhysXCooking_static_64","PhysXCommon_static_64", "PhysXFoundation_static_64"}

end

function get_include_string(includes)
    cmdString =" ";
    for k, v in ipairs(includes) do
        cmdString = cmdString.." -I "..tostring(v);
    end
    return cmdString
end

function commaficate(options)
    local result = "";
    local sep = "";
    for option in string.gmatch(options, "-%w+") do
        result = result..sep..tostring(option);
        sep = ","
    end
    return result;
end

function make_nvcc_command(nvccHostCompilerFlags, nvccFlags)
    
    local nvccPath = path.getabsolute("%{root}/_build/target-deps/cuda/bin/nvcc");
    local nvccHostCompilerVS =  path.getabsolute("%{root}/_build/host-deps/msvc/VC");

    if os.target() == "windows" then
        ext = ".obj"
        local compilerBindir = " --compiler-bindir "..nvccHostCompilerVS
        local buildString =  "\""..nvccPath.."\"".." "..nvccFlags..compilerBindir.." -Xcompiler="..nvccHostCompilerFlags.." -c %{get_include_string(cfg.includedirs)} %{file.abspath} -o %{cfg.objdir}/%{file.basename}"..ext
        buildmessage (buildString)
        buildcommands { buildString }
        buildoutputs { "%{cfg.objdir}/%{file.basename}"..ext }
    end
    if os.target() == "linux" then
        ext = ".o"
        local buildString =  "\""..nvccPath.."\" -std=c++14 "..nvccFlags.." -Xcompiler="..commaficate(nvccHostCompilerFlags).." -c %{get_include_string(cfg.includedirs)} %{file.abspath} -o %{cfg.objdir}/%{file.basename}"..ext
        buildcommands { "{MKDIR} %{cfg.objdir} ", buildString }
        buildoutputs { "%{cfg.objdir}/%{file.basename}"..ext }
    end
end


-- Define experience to test one particular extension.
-- @ext_name: Extension name.
-- @python_module: Python module name, if different from extension name. (optional)
function define_ext_test_experience(ext_name, python_module)
    local python_module = python_module or ext_name
    local script_dir_token = (os.target() == "windows") and "%~dp0" or "$SCRIPT_DIR"
    local args = {
        "--empty", -- Start empty kit
        "--enable omni.kit.test", -- We always need omni.kit.test extension as testing framework
        "--enable "..ext_name, -- Enable actual extension to test
        "--/exts/omni.kit.test/runTestsAndQuit=true", -- Run tests and quit
        "--/exts/omni.kit.test/includeTests/0='"..python_module..".*'", -- Only include tests from the python module
        "--ext-folder \""..script_dir_token.."/exts\" ",
        "--ext-folder \""..script_dir_token.."/apps\" ",
        "--/isaac/nucleus/default=\"omniverse://ov-isaac-qa\"", -- Default server used for isaac samples
        "--/omni.kit.plugin/syncUsdLoads=1", -- Force USD to fully load before rendering
        "--/persistent/app/viewport/displayOptions=0", -- Disable all ui elements in viewport
    }
    define_experience("tests-"..ext_name, {
        config_path = "",
        extra_args = table.concat(args, " "),
        define_project = false
    })
end

-- Isaac Sim needs this redefined here because we have a custom PXR_PLUGINPATH_NAME export to handle runtime USD
-- Write experience running .bat/.sh file, like _build\windows-x86_64\release\example.helloext.app.bat
function create_experience_runner(name, config_path, config, extra_args)
    if os.target() == "windows" then
        local bat_file_dir = root.."/_build/windows-x86_64/"..config
        local bat_file_path = bat_file_dir.."/"..name..".bat"
        local kit_bin_relative = path.getrelative(bat_file_dir, KIT_SDK_RESOLVED[config].."/_build/windows-x86_64/"..config)
        kit_bin_relative = path.normalize(kit_bin_relative):gsub("/", "\\")
        local config_path = (is_string_empty(config_path) and "") or "\"%%~dp0"..config_path.."\""
        local f = io.open(bat_file_path, 'w')
        f:write(string.format([[
@echo off
setlocal
call "%%~dp0%s\omniverse-kit.exe" %s %s %%*
        ]], kit_bin_relative, config_path, extra_args))
        f:close()
    else
        local sh_file_dir = root.."/_build/linux-x86_64/"..config
        local sh_file_path = sh_file_dir.."/"..name..".sh"
        local kit_bin_relative = path.getrelative(sh_file_dir, KIT_SDK_RESOLVED[config].."/_build/linux-x86_64/"..config)
        local usd_ext_isaac_schema_path = root.."/_build/target-deps/usd_ext_isaac/"..config.."/share/usd/plugins/*/resources/"
        kit_bin_relative = path.normalize(kit_bin_relative)
        local config_path = (is_string_empty(config_path) and "") or "\"$SCRIPT_DIR/"..config_path.."\""
        local f = io.open(sh_file_path, 'w')
        f:write(string.format([[
#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
export PXR_PLUGINPATH_NAME="%s":$PXR_PLUGINPATH_NAME
"$SCRIPT_DIR/%s/kit" %s %s $@
        ]], usd_ext_isaac_schema_path, kit_bin_relative, config_path, extra_args))
        f:close()
        os.chmod(sh_file_path, 755)
    end
end