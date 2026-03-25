// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#include <carb/BindingsPythonUtils.h>

#include <isaacsim/xr/input_devices/IsaacSimHandTrackerCAPI.h>

#include <array>
#include <string>

// Python bindings module that exposes the hand-tracker C API and constants to Python.
CARB_BINDINGS("isaacsim.xr.input_devices.python")

// C-API exported by the plugin shared library (implemented in IsaacSimHandTrackerPlugin.cpp)
extern "C"
{
    bool IsaacSimHandTrackerPlugin_Load(const char* overrideLibraryPath); // NOLINT(readability-identifier-naming)
    void IsaacSimHandTrackerPlugin_Unload(); // NOLINT(readability-identifier-naming)
    bool IsaacSimHandTrackerPlugin_Initialize(); // NOLINT(readability-identifier-naming)
    bool IsaacSimHandTrackerPlugin_GetData(IsaacSimHandJointPose* outJointPoses,
                                           int outJointPoseCount); // NOLINT(readability-identifier-naming)
    void IsaacSimHandTrackerPlugin_Shutdown(); // NOLINT(readability-identifier-naming)
}

// Register enums, constants, and hand-tracker control/data functions.
void bindIsaacSimHandTrackerPlugin(py::module_& m)
{
    // Expose enums and constants
    py::enum_<IsaacSimHandJoints>(m, "IsaacSimHandJoints")
        .value("PALM", ISAACSIM_HAND_JOINT_PALM)
        .value("WRIST", ISAACSIM_HAND_JOINT_WRIST)
        .value("THUMB_METACARPAL", ISAACSIM_HAND_JOINT_THUMB_METACARPAL)
        .value("THUMB_PROXIMAL", ISAACSIM_HAND_JOINT_THUMB_PROXIMAL)
        .value("THUMB_DISTAL", ISAACSIM_HAND_JOINT_THUMB_DISTAL)
        .value("THUMB_TIP", ISAACSIM_HAND_JOINT_THUMB_TIP)
        .value("INDEX_METACARPAL", ISAACSIM_HAND_JOINT_INDEX_METACARPAL)
        .value("INDEX_PROXIMAL", ISAACSIM_HAND_JOINT_INDEX_PROXIMAL)
        .value("INDEX_INTERMEDIATE", ISAACSIM_HAND_JOINT_INDEX_INTERMEDIATE)
        .value("INDEX_DISTAL", ISAACSIM_HAND_JOINT_INDEX_DISTAL)
        .value("INDEX_TIP", ISAACSIM_HAND_JOINT_INDEX_TIP)
        .value("MIDDLE_METACARPAL", ISAACSIM_HAND_JOINT_MIDDLE_METACARPAL)
        .value("MIDDLE_PROXIMAL", ISAACSIM_HAND_JOINT_MIDDLE_PROXIMAL)
        .value("MIDDLE_INTERMEDIATE", ISAACSIM_HAND_JOINT_MIDDLE_INTERMEDIATE)
        .value("MIDDLE_DISTAL", ISAACSIM_HAND_JOINT_MIDDLE_DISTAL)
        .value("MIDDLE_TIP", ISAACSIM_HAND_JOINT_MIDDLE_TIP)
        .value("RING_METACARPAL", ISAACSIM_HAND_JOINT_RING_METACARPAL)
        .value("RING_PROXIMAL", ISAACSIM_HAND_JOINT_RING_PROXIMAL)
        .value("RING_INTERMEDIATE", ISAACSIM_HAND_JOINT_RING_INTERMEDIATE)
        .value("RING_DISTAL", ISAACSIM_HAND_JOINT_RING_DISTAL)
        .value("RING_TIP", ISAACSIM_HAND_JOINT_RING_TIP)
        .value("LITTLE_METACARPAL", ISAACSIM_HAND_JOINT_LITTLE_METACARPAL)
        .value("LITTLE_PROXIMAL", ISAACSIM_HAND_JOINT_LITTLE_PROXIMAL)
        .value("LITTLE_INTERMEDIATE", ISAACSIM_HAND_JOINT_LITTLE_INTERMEDIATE)
        .value("LITTLE_DISTAL", ISAACSIM_HAND_JOINT_LITTLE_DISTAL)
        .value("LITTLE_TIP", ISAACSIM_HAND_JOINT_LITTLE_TIP);

    py::enum_<IsaacSimHandJointLocationFlags>(m, "IsaacSimHandJointLocationFlags", py::arithmetic())
        .value("POSITION_VALID", ISAACSIM_HAND_JOINT_LOCATION_FLAGS_POSITION_VALID)
        .value("ORIENTATION_VALID", ISAACSIM_HAND_JOINT_LOCATION_FLAGS_ORIENTATION_VALID)
        .value("POSITION_TRACKED", ISAACSIM_HAND_JOINT_LOCATION_FLAGS_POSITION_TRACKED)
        .value("ORIENTATION_TRACKED", ISAACSIM_HAND_JOINT_LOCATION_FLAGS_ORIENTATION_TRACKED);

    m.attr("ISAACSIM_HAND_JOINT_COUNT") = py::int_(ISAACSIM_HAND_JOINT_COUNT);
    m.attr("ISAACSIM_HAND_COUNT") = py::int_(ISAACSIM_HAND_COUNT);

    // Hand-tracker plugin control and data accessors
    m.def(
        "handtracker_load",
        [](py::object overrideLibraryPath)
        {
            const char* pathCStr = nullptr;
            std::string path;
            if (!overrideLibraryPath.is_none())
            {
                path = py::cast<std::string>(overrideLibraryPath);
                pathCStr = path.c_str();
            }
            return IsaacSimHandTrackerPlugin_Load(pathCStr);
        },
        py::arg("override_library_path") = py::none(),
        R"doc(Load the hand-tracker shared library.

If `override_library_path` is provided, that path is attempted first; otherwise
environment variables may be used by the plugin loader:
- ISAACSIM_HANDTRACKER_LIB: absolute path
- ISAACSIM_HANDTRACKER_NAME: base name (tries lib<name>.so / <name>.dll)

Returns True on success.)doc");

    m.def(
        "handtracker_unload", []() { IsaacSimHandTrackerPlugin_Unload(); },
        R"doc(Unload the hand tracker shared library.)doc");

    m.def(
        "handtracker_initialize", []() { return IsaacSimHandTrackerPlugin_Initialize(); },
        R"doc(Initialize the hand tracker device via the loaded library.)doc");

    m.def(
        "handtracker_get_data",
        []()
        {
            constexpr size_t kTotal =
                static_cast<size_t>(ISAACSIM_HAND_COUNT) * static_cast<size_t>(ISAACSIM_HAND_JOINT_COUNT);
            std::array<IsaacSimHandJointPose, kTotal> poses{};
            bool ok = IsaacSimHandTrackerPlugin_GetData(poses.data(), static_cast<int>(poses.size()));
            py::list hands;
            if (ok)
            {
                for (int hand = 0; hand < ISAACSIM_HAND_COUNT; ++hand)
                {
                    py::list joints;
                    const int base = hand * ISAACSIM_HAND_JOINT_COUNT;
                    for (int j = 0; j < ISAACSIM_HAND_JOINT_COUNT; ++j)
                    {
                        const int idx = base + j;
                        const IsaacSimHandJointPose& p = poses[static_cast<size_t>(idx)];
                        py::dict d;
                        d["hand"] = hand;
                        d["joint"] = j;
                        d["position"] = py::make_tuple(p.position[0], p.position[1], p.position[2]);
                        d["orientation"] =
                            py::make_tuple(p.orientation[0], p.orientation[1], p.orientation[2], p.orientation[3]);
                        d["radius"] = p.radius;
                        d["location_flags"] = p.locationFlags;
                        joints.append(std::move(d));
                    }
                    hands.append(std::move(joints));
                }
            }
            return py::make_tuple(ok, hands);
        },
        R"doc(Get latest joint data for both hands.

Returns a tuple `(success: bool, hands: List[List[Dict]]]`.
`hands[hand][joint]` contains:
- `hand` (int)
- `joint` (int)
- `position` (x, y, z)
- `orientation` (x, y, z, w)
- `radius` (float)
- `location_flags` (int)
)doc");

    m.def(
        "handtracker_shutdown", []() { IsaacSimHandTrackerPlugin_Shutdown(); },
        R"doc(Shutdown the hand tracker device.)doc");
}


namespace
{
PYBIND11_MODULE(_isaac_xr_input_devices, m)
{
    // We use carb data types, must import bindings for them
    auto carbModule = py::module::import("carb");

    // Register Hand Tracker plugin bindings (C API wrapper)
    bindIsaacSimHandTrackerPlugin(m);
}
}
