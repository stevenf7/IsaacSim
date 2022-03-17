// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "ros/ros.h"

#include <OgnROS1NodeDatabase.h>

class OgnROS1Node
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnROS1NodeDatabase::sInternalState<OgnROS1Node>(nodeObj);
        state.mInitialized = false;
    }

    static bool compute(OgnROS1NodeDatabase& db)
    {
        auto& state = db.internalState<OgnROS1Node>();

        // Always make sure there is a valid ROS master, Reset if its not valid
        if (!ros::master::check())
        {
            state.mInitialized = false;
            state.mNodeHandle.reset();
            db.outputs.nodeHandle() = 0;
            return false;
        }
        // If we haven't initialized, or were reset due to the ros master check failing, re-initialize
        if (!state.mInitialized)
        {
            const auto& name = db.inputs.nodeName();
            std::string result;
            if (!ros::names::validate(name, result))
            {
                db.logError("Topic name %s not valid %s", name.data(), result.c_str());
                db.outputs.nodeHandle() = 0;
                return false;
            }

            state.mNodeHandle = std::make_unique<ros::NodeHandle>(name);
            state.mInitialized = true;
            db.outputs.nodeHandle() = reinterpret_cast<uint64_t>(state.mNodeHandle.get());
            return true;
        }

        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS1NodeDatabase::sInternalState<OgnROS1Node>(nodeObj);
        state.mInitialized = false;
        state.mNodeHandle.reset();
    }

private:
    bool mInitialized = false;
    std::unique_ptr<ros::NodeHandle> mNodeHandle;
};

REGISTER_OGN_NODE()
