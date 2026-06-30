-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
-- http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

if os.target() == "linux" then
    local ext = get_current_extension_info()
    local ogn = get_ogn_project_information(ext, "isaacsim/zmq/core")
    project_ext(ext)

    -- Protobuf codegen: run protoc on all .proto files before C++ compile
    -- C++ generated files land in _build/.../isaacsim.zmq.core/generated/proto/
    -- Python generated files land alongside the extension's Python package
    local proto_out_dir = ext.bin_dir .. "/../generated/proto"
    local proto_python_out_dir = ext.target_dir .. "/isaacsim/zmq/core"
    local proto_src_dir = "%{root}/source/extensions/isaacsim.zmq.core/proto"
    local protoc_bin = "%{root}/_build/target-deps/protobuf/bin/protoc"

    -- Build the backend library
    project_with_location("isaacsim.zmq.core")
    targetdir(ext.bin_dir)
    kind("SharedLib")
    language("C++")
    cppdialect("C++17")

    pic("On")
    staticruntime("Off")

    add_files("impl", "library/backend")
    add_files("iface", "include")

    -- Include generated proto headers
    includedirs {
        "%{root}/source/extensions/isaacsim.zmq.core/include",
        "%{root}/source/extensions/isaacsim.core.includes/include",
        "%{root}/_build/target-deps/zmq/include",
        "%{root}/_build/target-deps/cppzmq/include",
        "%{root}/_build/target-deps/protobuf/include",
        "%{root}/_build/target-deps/abseil/include",
        proto_out_dir,
    }

    libdirs {
        "%{root}/_build/target-deps/zmq/lib",
        "%{root}/_build/target-deps/protobuf/lib",
        "%{root}/_build/target-deps/abseil/lib",
    }

    -- Dynamic link to zmq only; protobuf and abseil are statically linked below
    links { "zmq" }

    linkoptions {
        "-Wl,--allow-multiple-definition",
        "-Wl,--whole-archive",
        "%{root}/_build/target-deps/abseil/lib/libabsl_*.a",
        "%{root}/_build/target-deps/protobuf/lib/lib*.a",
        "-Wl,--no-whole-archive",
        -- Hide static-lib symbols (abseil, protobuf) so they don't conflict
        -- with Kit's own abseil when both are loaded in the same process.
        "-Wl,--exclude-libs,ALL",
        -- Force libz.so into the NEEDED section (protobuf uses zlib for compression;
        -- --as-needed would otherwise strip the dependency since the symbol may appear
        -- resolved from a previously linked archive).
        "-Wl,--no-as-needed,-lz,--as-needed",
    }

    -- Feed the .proto files to the custom build rule below. The generated .pb.cc
    -- are NOT listed here: premake already compiles them via the rule's buildoutputs.
    -- Listing them as well made premake compile each proto twice (duplicate object).
    files {
        proto_src_dir .. "/clock.proto",
        proto_src_dir .. "/image.proto",
        proto_src_dir .. "/bbox2d.proto",
        proto_src_dir .. "/camera_params.proto",
        proto_src_dir .. "/update_prim_attribute.proto",
        proto_src_dir .. "/joint_states.proto",
        proto_src_dir .. "/joint_command.proto",
    }

    -- Custom build rule: .proto → .pb.cc + .pb.h
    -- gmake generates a make target for each .proto so the .pb.cc deps resolve correctly.
    filter "files:**.proto"
        buildmessage "Generating protobuf: %{file.name}"
        buildcommands {
            "mkdir -p " .. proto_out_dir,
            "mkdir -p " .. proto_python_out_dir,
            protoc_bin .. " --proto_path=" .. proto_src_dir ..
                " --cpp_out=" .. proto_out_dir ..
                " --python_out=" .. proto_python_out_dir ..
                " %{file.abspath}",
        }
        buildoutputs {
            proto_out_dir .. "/%{file.basename}.pb.cc",
            proto_out_dir .. "/%{file.basename}.pb.h",
            proto_python_out_dir .. "/%{file.basename}_pb2.py",
        }
    filter {}

    filter { "system:linux" }
    disablewarnings { "error=pragmas" }
    -- -Wno-undef silences the toolchain's global -Wundef on the generated protobuf
    -- sources, which reference macros (e.g. PROTOBUF_ENABLE_DEBUG_LOGGING_MAY_LEAK_PII)
    -- that protobuf leaves undefined in non-debug builds. Applied at project scope (not
    -- a per-file filter) so it reaches the compiled .pb.o via ALL_CXXFLAGS; safe here
    -- since the hand-written sources don't rely on -Wundef.
    buildoptions { "-fvisibility=default", "-Wno-undef" }
    linkoptions { "-Wl,--export-dynamic", "-Wl,-rpath,'$$ORIGIN/lib'" }
    filter {}
    filter { "system:windows" }
    buildoptions("-D_CRT_SECURE_NO_WARNINGS")
    filter {}

    filter { "configurations:debug" }
    defines { "_DEBUG" }
    filter { "configurations:release" }
    defines { "NDEBUG" }
    filter {}

    -- Bundle libzmq.so and libz.so alongside the extension binary.
    -- libz is needed at runtime because protobuf (statically linked) uses zlib for compression.
    repo_build.prebuild_copy {
        { "%{root}/_build/target-deps/zmq/lib/libzmq.so*", ext.bin_dir .. "/lib/" },
        { "%{root}/_build/target-deps/usd/release/lib/libz.so*", ext.bin_dir .. "/lib/" },
    }

    repo_build.prebuild_link {
        { "docs",          ext.target_dir .. "/docs" },
        { "include",       ext.target_dir .. "/include" },
        { "python/impl",   ext.target_dir .. "/isaacsim/zmq/core/impl" },
        { "python/tests",  ext.target_dir .. "/isaacsim/zmq/core/tests" },
        -- Bundle the protobuf (and pyzmq) Python runtime so the generated
        -- *_pb2 schemas shipped in this package are importable on their own.
        { "%{root}/_build/target-deps/pip_zmq_prebundle", ext.target_dir .. "/pip_prebundle" },
    }

    repo_build.prebuild_copy {
        { "python/__init__.py",            ext.target_dir .. "/isaacsim/zmq/core/" },
    }

    -- Python bindings for the core library
    project_ext_bindings {
        ext = ext,
        project_name = ogn.python_project,
        module = "_isaacsim_zmq_core",
        src = "bindings/isaacsim.zmq.core",
        target_subdir = "isaacsim/zmq/core/bindings",
    }
    add_files("bindings", "bindings/isaacsim.zmq.core/*.*")

    includedirs {
        "%{root}/source/extensions/isaacsim.zmq.core/include",
        "%{root}/_build/target-deps/zmq/include",
        "%{root}/_build/target-deps/cppzmq/include",
        "%{root}/_build/target-deps/protobuf/include",
        proto_out_dir,
    }

    libdirs {
        ext.bin_dir,
        "%{root}/_build/target-deps/zmq/lib",
    }

    links { "isaacsim.zmq.core", "zmq" }

else
    print("SKIPPING BUILD - Only supported on linux-x86_64")
end
