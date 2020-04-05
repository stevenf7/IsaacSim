// Copyright (c) 2018-2019, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/ros_bridge/RosBridge.h>
#include <pybind11/pybind11/numpy.h>

CARB_BINDINGS("omni.isaac.ros_bridge.python")

namespace omni
{
namespace isaac
{
namespace ros_bridge
{
}
}
}

namespace
{

PYBIND11_MODULE(_ros_bridge, m)
{
    using namespace carb;
    using namespace omni::isaac::ros_bridge;

    m.doc() = "Isaac ROS bridge bindings";

    {
        defineInterfaceClass<RosBridge>(m, "Isaac RosBridge", "acquire_rosbridge_interface", "release_rosbridge_interface")
            .def("add_ros_node", wrapInterfaceFunction(&RosBridge::addRosNode))
            .def("add_ros_event", wrapInterfaceFunction(&RosBridge::addRosEvent))
            .def("delete_ros_node", wrapInterfaceFunction(&RosBridge::deleteRosNode))
            .def("delete_ros_event", wrapInterfaceFunction(&RosBridge::deleteRosEvent))
            .def("set_clock_state", wrapInterfaceFunction(&RosBridge::setClockState))
            .def("get_json_string", wrapInterfaceFunction(&RosBridge::getJsonString))
            .def("parse_json_string", wrapInterfaceFunction(&RosBridge::parseJsonString));

        py::enum_<RosEventType>(m, "EventType", py::arithmetic(), "Types of ROS events supported by the bridge")
            .value("NONE", eRosEventNone, "Invalid event type")
            .value("PUBLISH", eRosEventPublish, "Publish messages")
            .value("SUBSCRIBE", eRosEventSubscribe, "Subscribe to messages")
            .value("SERVICE", eRosEventService, "Service")
            .value("PERIODIC", eRosEventPeriodic, "Periodic")
            .export_values();

        py::enum_<RosMessageType>(m, "MessageType", py::arithmetic(), "Types of ROS Messages supported by the bridge")
            .value("NONE", eRosMessageNone, "Invalid message type")
            .value("EMPTY", eRosMessageEmpty, "Empty Message")
            .value("POSE", eRosMessagePose, "3d pose")
            .value("JOINT_STATE", eRosMessageJointState, "Joint States")
            .value("TF", eRosMessageTf, "Pose Tree")
            .value("IMAGE", eRosMessageImage, "Image")
            .value("CAMERA_INFO", eRosMessageCameraInfo, "Camera Information")
            .value("BOUNDING_BOX", eRosMessageBoundingBox, "Bounding BOx")
            .value("RANGE_SCAN", eRosMessageRangeScan, "Range Scan")
            .export_values();

        m.def("event_from_string", [](std::string event_str) {
            RosEventType mevent = eRosEventNone;
            if (event_str == "NONE")
            {
                mevent = eRosEventNone;
            }
            else if (event_str == "PUBLISH")
            {
                mevent = eRosEventPublish;
            }
            else if (event_str == "SUBSCRIBE")
            {
                mevent = eRosEventSubscribe;
            }
            else if (event_str == "SERVICE")
            {
                mevent = eRosEventService;
            }
            else if (event_str == "PERIODIC")
            {
                mevent = eRosEventPeriodic;
            }

            return mevent;
        });

        m.def("message_from_string", [](std::string message_str) {
            RosMessageType mtype = eRosMessageNone;
            if (message_str == "NONE")
            {
                mtype = eRosMessageNone;
            }
            else if (message_str == "EMPTY")
            {
                mtype = eRosMessageEmpty;
            }
            else if (message_str == "JOINT_STATE")
            {
                mtype = eRosMessageJointState;
            }
            else if (message_str == "POSE")
            {
                mtype = eRosMessagePose;
            }
            else if (message_str == "TF")
            {
                mtype = eRosMessageTf;
            }
            else if (message_str == "IMAGE")
            {
                mtype = eRosMessageImage;
            }
            else if (message_str == "CAMERA_INFO")
            {
                mtype = eRosMessageCameraInfo;
            }
            else if (message_str == "BOUNDING_BOX")
            {
                mtype = eRosMessageBoundingBox;
            }
            else if (message_str == "RANGE_SCAN")
            {
                mtype = eRosMessageRangeScan;
            }
            return mtype;
        });
    }
}
}
