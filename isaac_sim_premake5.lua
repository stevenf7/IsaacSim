
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
        disablewarnings {"error=pragmas"}
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

    links { "PhysXExtensions_static_64", "PhysX_static_64", "PhysXPvdSDK_static_64","PhysXCooking_static_64","PhysXCommon_static_64", "PhysXFoundation_static_64", "PhysXVehicle_static_64"}

    includedirs {
        "%{root}/_build/target-deps/physx/include",
        "%{root}/_build/target-deps/pxshared/include",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
    }

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

-- Helper function to implement a build step that preprocesses .cu files (CUDA code) for compilation
-- TODO: the cross-compilation case is missed here and that forces compilation errors on TC
function make_nvcc_command(nvccPath, nvccHostCompilerVS, nvccHostCompilerFlags, nvccFlags)
    if os.target() == "windows" then
        ext = ".obj"
        local compilerBindir = " --compiler-bindir "..nvccHostCompilerVS
        local buildString =  "\""..nvccPath.."\"".." "..nvccFlags..compilerBindir.." -Xcompiler="..nvccHostCompilerFlags.." -c -I "..carbSDKInclude.." %{get_include_string(cfg.includedirs)} %{file.abspath} -o %{cfg.objdir}/%{file.basename}"..ext
        buildmessage (buildString)
        buildcommands { buildString }
        buildoutputs { "%{cfg.objdir}/%{file.basename}"..ext }
    end
    if os.target() == "linux" then
        ext = ".o"
        local buildString =  "\""..nvccPath.."\" -std=c++14 "..nvccFlags.." -Xcompiler="..commaficate(nvccHostCompilerFlags).." -c -I "..carbSDKInclude.." %{get_include_string(cfg.includedirs)} %{file.abspath} -o %{cfg.objdir}/%{file.basename}"..ext
        buildcommands { "{MKDIR} %{cfg.objdir} ", buildString }
        buildoutputs { "%{cfg.objdir}/%{file.basename}"..ext }
    end
end

-- Helper function to call in your project definition when you have .cu files to process.
-- This sets up the CUDA compilation for all files within your project using the correct rules for each configuration.
function add_cuda_dependencies()
    -- First the build rules for CUDA files
    filter { "files:**.cu", "system:windows", "configurations:debug" }
        make_nvcc_command(nvccPath, nvccHostCompilerVS, "/MDd", "-g -G")
    filter { "files:**.cu", "system:windows", "configurations:release" }
        make_nvcc_command(nvccPath, nvccHostCompilerVS, "/MD", "")
    filter { "files:**.cu", "system:linux", "configurations:debug" }
        make_nvcc_command(nvccPath, nvccHostCompilerVS, "-fPIC -g", "-g")
    filter { "files:**.cu", "system:linux", "configurations:release" }
        make_nvcc_command(nvccPath, nvccHostCompilerVS, "-fPIC", "")
    filter {}

    -- link against CUDA runtime static library.
    links { "cudart_static" }

    -- Add in the library directories
    filter { "system:linux" }
        -- lib dir stubs in case you link against 'cuda'.
        libdirs { target_deps.."/cuda/lib64/stubs" }
        -- lib dir in case you link against 'cudart_static'.
        libdirs { target_deps.."/cuda/lib64/" }

        -- linking to cudart_static requires libpthread, libdl, and librt
        -- https://gitlab.kitware.com/cmake/cmake/-/issues/20249
        buildoptions { "-pthread" }
        links { "dl", "pthread", "rt" }
    filter { "system:windows" }
        libdirs { target_deps.."/cuda/lib/x64" }
    filter {}

    -- CUDA-specific include directory
    includedirs { target_deps.."/cuda/include" }
end

-- Define experience to test one particular extension.
-- @ext_name: Extension name.
-- @python_module: Python module name, if different from extension name. (optional)
function define_ext_test_experience(ext_name, args)
    local args = args or {}

    local python_module = get_value_or_default(args, "python_module", ext_name)
    local script_dir_token = (os.target() == "windows") and "%~dp0" or "$SCRIPT_DIR"
    local test_args = {
        "--empty", -- Start empty kit
        "--enable omni.kit.test", -- We always need omni.kit.test extension as testing framework
        "--/exts/omni.kit.test/testExtEnableProfiler=0",
        "--/exts/omni.kit.test/testExtDefaultTimeout=600",
        "--/exts/omni.kit.test/testExtArgs/0=\"--no-window\"",
        "--/exts/omni.kit.test/testExtArgs/1=\"--allow-root\"",
        "--/exts/omni.kit.test/testExtArgs/2=\"--/exts/omni.kit.test/testExtDefaultTimeout=600\"",
        "--/exts/omni.kit.test/testExtApp=\""..script_dir_token.."/../apps/omni.isaac.sim.test_ext.kit\"",
        -- "--/exts/omni.kit.test/runTestsAndQuit=true", -- Run tests and quit
        "--/exts/omni.kit.test/testExts/0='"..python_module.."'", -- Only include tests from the python module
        "--ext-folder \""..script_dir_token.."/../exts\" ",
        "--ext-folder \""..script_dir_token.."/../extscache\" ",
        "--ext-folder \""..script_dir_token.."/../apps\" ",
        "--/app/enableStdoutOutput=0",  -- this app just runs the test command, hide its output
        "--no-window",
        "--allow-root",
    }
    -- Allow passing additional args
    local extra_test_args = get_value_or_default(args, "extra_test_args", {})
    test_args = concat_arrays(test_args, extra_test_args)

    local suite = get_value_or_default(args, "suite", EXT_TEST_TEST_SUITE_DEFAULT)

    local exp_args = {
        config_path = "",
        extra_args = table.concat(test_args, " "),
        define_project = false
    }
    exp_args = merge_tables(exp_args, args)

    local test_name = suite and string.format("tests-%s-%s", suite, ext_name) or ("tests-"..ext_name)
    define_test_experience(test_name, exp_args)
end


-- Define Kit experience. Different ways to run kit with particular config
function define_test_experience(name, args)
    local args = args or {}
    local experience = args.experience or name..".json"
    local config_path = get_value_or_default(args, "config_path", "experiences/"..experience)
    local extra_args = args.extra_args or ""
    -- Write bat and sh files as another way to run them:
    for _, config in ipairs(ALL_CONFIGS) do
        local kit_sdk_config = get_value_or_default(args, "kit_sdk_config", kit_sdk_config)
        if kit_sdk_config == "%{config}" then 
            kit_sdk_config = config
        end
        create_test_experience_runner(name, config_path, config, kit_sdk_config, extra_args)
    end
end

-- Write experience running .bat/.sh file, like _build\windows-x86_64\release\example.helloext.app.bat
function create_test_experience_runner(name, config_path, config, kit_sdk_config, extra_args)
    local os_target = os.target()
    if os_target == "windows" then
        local bat_file_dir = root.."/_build/windows-x86_64/"..config.."/tests"
        local bat_file_path = bat_file_dir.."/"..name..".bat"
        local kit_bin_abs = string_fmt_vars_recursive(kit_sdk_bin_dir, {
            root=root, config=config, kit_sdk=kit_sdk, kit_sdk_config=kit_sdk_config, platform="windows-x86_64" 
        })
        local kit_bin_relative = path.normalize(path.getrelative(bat_file_dir, kit_bin_abs)):gsub("/", "\\")
        local config_path = (is_string_empty(config_path) and "") or "\"%%~dp0"..config_path.."\""
        local f = io.open(bat_file_path, 'w')
        f:write(string.format(KIT_RUNNER_SHELL_TEMPLATE[os_target], kit_bin_relative, config_path, extra_args))
        f:close()
    else
        local sh_file_dir = root.."/_build/linux-x86_64/"..config.."/tests"
        local sh_file_path = sh_file_dir.."/"..name..".sh"
        local kit_bin_abs = string_fmt_vars_recursive(kit_sdk_bin_dir, {
            root=root, config=config, kit_sdk=kit_sdk, kit_sdk_config=kit_sdk_config, platform="linux-x86_64" 
        })
        local kit_bin_relative = path.normalize(path.getrelative(sh_file_dir, kit_bin_abs))
        local config_path = (is_string_empty(config_path) and "") or "\"$SCRIPT_DIR/"..config_path.."\""
        local f = io.open(sh_file_path, 'w')
        f:write(string.format(KIT_RUNNER_SHELL_TEMPLATE[os_target], kit_bin_relative, config_path, extra_args))
        f:close()
        os.chmod(sh_file_path, 755)
    end
end

function python_sample_test(name, sample_path, args)
    local extra_args = args or ""
    for _, config in ipairs(ALL_CONFIGS) do
        create_python_sample_runner(name, sample_path, config, extra_args)
    end
end
function create_python_sample_runner(name, sample_path, config, extra_args)
    if os.target() == "linux" then
        local sh_file_dir = root.."/_build/linux-x86_64/"..config.."/tests"
        local sh_file_path = sh_file_dir.."/"..name..".sh"
        local f = io.open(sh_file_path, 'w')
        print(sh_file_path)
        f:write(string.format([[
#!/bin/bash
set -e
echo "##teamcity[testStarted name='%s']" 
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
SAMPLE_DIR=$SCRIPT_DIR/../
"$SCRIPT_DIR/../python.sh" -m pip install -r $SCRIPT_DIR/../requirements.txt
"$SCRIPT_DIR/../python.sh" $SAMPLE_DIR/%s %s $@
echo "##teamcity[testFinished name='%s']" 
        ]], sample_path, sample_path, extra_args, sample_path, sample_path))
        f:close()
        os.chmod(sh_file_path, 755)
    else
        local bat_file_dir = root.."/_build/windows-x86_64/"..config.."/tests"
        local bat_file_path = bat_file_dir.."/"..name..".bat"
        
        local f = io.open(bat_file_path, 'w')
        print(bat_file_path)
        f:write(string.format([[
@echo off
setlocal
echo "##teamcity[testStarted name='%s']"
call "%%~dp0..\python.bat" -m pip install -r "%%~dp0..\requirements.txt"
call "%%~dp0..\python.bat" "%%~dp0..\%s" %s %%*
echo "##teamcity[testFinished name='%s']" 
        ]], name, sample_path, extra_args, sample_path, name))
        f:close()
    end
end

function jupyter_sample_test(name, sample_path, args)
    local extra_args = args or ""
    for _, config in ipairs(ALL_CONFIGS) do
        jupyter_sample_runner(name, sample_path, config, extra_args)
    end
end
function jupyter_sample_runner(name, sample_path, config, extra_args)
    if os.target() == "linux" then
        local sh_file_dir = root.."/_build/linux-x86_64/"..config.."/tests"
        local sh_file_path = sh_file_dir.."/"..name..".sh"
        local f = io.open(sh_file_path, 'w')
        print(sh_file_path)
        f:write(string.format([[
#!/bin/bash
set -e
echo "##teamcity[testStarted name='%s']" 
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
SAMPLE_DIR=$SCRIPT_DIR/../
"$SCRIPT_DIR/../jupyter_notebook.sh" test $SAMPLE_DIR/%s %s $@
echo "##teamcity[testFinished name='%s']" 
        ]], name, sample_path, extra_args, sample_path, name))
        f:close()
        os.chmod(sh_file_path, 755)
    end
end

-- Template Used to generate all the kit.bat, test.bat and other batch/shell files
-- format are: kit_bin_relative, config_path, extra_args
KIT_RUNNER_SHELL_TEMPLATE = {
    ["windows"] = [[
@echo off
setlocal
call "%%~dp0%s\kit.exe" %s %s %%*
]],
    ["linux"] = [[
#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
export RESOURCE_NAME="IsaacSim"
exec "$SCRIPT_DIR/%s/kit" %s %s "$@"
]]
}


function python_script_test(name, script)
    for _, config in ipairs(ALL_CONFIGS) do
        create_python_script_runner(name, script, config)
    end
end
function create_python_script_runner(name, script, config)
    if os.target() == "linux" then
        local sh_file_dir = root.."/_build/linux-x86_64/"..config.."/tests"
        local sh_file_path = sh_file_dir.."/"..name..".sh"
        local f = io.open(sh_file_path, 'w')
        print(sh_file_path)
        f:write(string.format([[
#!/bin/bash
set -e
echo "##teamcity[testStarted name='%s']" 
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
SAMPLE_DIR=$SCRIPT_DIR/../
"$SCRIPT_DIR/../python.sh"  %s $@
echo "##teamcity[testFinished name='%s']" 
        ]], script, script, script))
        f:close()
        os.chmod(sh_file_path, 755)
    else
        local bat_file_dir = root.."/_build/windows-x86_64/"..config.."/tests"
        local bat_file_path = bat_file_dir.."/"..name..".bat"
        
        local f = io.open(bat_file_path, 'w')
        print(bat_file_path)
        f:write(string.format([[
@echo off
setlocal
echo "##teamcity[testStarted name='%s']"
"%%~dp0..\python.bat" %s %%*
echo "##teamcity[testFinished name='%s']" 
        ]], name, script, name))
        f:close()
    end
end


function docker_test(name, script, args)
    local extra_args = args or ""
    for _, config in ipairs(ALL_CONFIGS) do
        docker_test_runner(name, script, config, extra_args)
    end
end
function docker_test_runner(name, script, config, extra_args)
    if os.target() == "linux" then
        local sh_file_dir = root.."/_build/linux-x86_64/"..config.."/tests"
        local sh_file_path = sh_file_dir.."/"..name..".sh"
        local f = io.open(sh_file_path, 'w')
        print(sh_file_path)
        f:write(string.format([[
#!/bin/bash

set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
docker ps -q --filter "name=isaac-sim" | grep -q . && docker kill isaac-sim
docker run --name isaac-sim --entrypoint bash --gpus all -e "ACCEPT_EULA=Y" --rm --network=host \
-v $SCRIPT_DIR/..:/isaac-sim:rw \
-e "OMNI_USER=dockeruser" -e "OMNI_PASS=dockeruser" \
-e "OMNI_SERVER=omniverse://isaac-dev.ov.nvidia.com" \
-v /etc/vulkan/icd.d/nvidia_icd.json:/etc/vulkan/icd.d/nvidia_icd.json \
-v /etc/vulkan/implicit_layer.d/nvidia_layers.json:/etc/vulkan/implicit_layer.d/nvidia_layers.json \
-v /usr/share/glvnd/egl_vendor.d/10_nvidia.json:/usr/share/glvnd/egl_vendor.d/10_nvidia.json \
gitlab-master.nvidia.com:5005/isaac/omni_isaac_sim/isaac-sim:latest-develop \
-c "%s %s"
        ]], script, extra_args))
        f:close()
        os.chmod(sh_file_path, 755)
    end
end