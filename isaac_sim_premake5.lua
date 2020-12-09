
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