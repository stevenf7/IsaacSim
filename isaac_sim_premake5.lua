
function include_physx()
    -- Which physx library type to use in release mode
    physx_libs = "profile"
    
    if configuration == "debug" then
        physx_libs = "debug"
    end

    filter { "configurations:debug" }
        defines {  "PX_PHYSX_STATIC_LIB", "_DEBUG" }
    filter { "configurations:release" }
        defines {  "PX_PHYSX_STATIC_LIB", "NDEBUG" }

    filter { "system:windows", "platforms:x86_64" }
        libdirs { "%{root}/_build/target-deps/nvtx/lib/x64" }
        libdirs { 
            "%{root}/_build/target-deps/physx/bin/win.x86_64.vc141.md/"..physx_libs, 
            "%{root}/_build/target-deps/vhacd/bin/win.x86_64.vc141.md/%{config}" 
        }
        links { "nvToolsExt64_1"}
    filter {}

    filter { "system:linux", "platforms:x86_64" }
        libdirs { "%{root}/_build/target-deps/nvtx/lib/x64" }
        links { "nvToolsExt"}
        libdirs { 
            "%{root}/_build/target-deps/physx/bin/linux.clang/"..physx_libs, 
            "%{root}/_build/target-deps/vhacd/bin/linux.clang/%{config}" 
        }

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