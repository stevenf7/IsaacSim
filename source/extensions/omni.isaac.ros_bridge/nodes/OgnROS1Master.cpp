// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "ros/ros.h"

#include <OgnROS1MasterDatabase.h>

class OgnROS1Master
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnROS1MasterDatabase::sInternalState<OgnROS1Master>(nodeObj);
        state.mInitialized = false;
    }

    static bool compute(OgnROS1MasterDatabase& db)
    {
        auto& state = db.internalState<OgnROS1Master>();

        // Always make sure there is a valid ROS master, Reset if its not valid
        if (!ros::master::check())
        {
            state.mInitialized = false;
            db.outputs.status() = false;
            db.outputs.host() = "";
            db.outputs.port() = 0;
            db.outputs.uri() = "";
            return false;
        }
        state.mInitialized = true;
        db.outputs.status() = true;
        db.outputs.host() = ros::master::getHost();
        db.outputs.port() = ros::master::getPort();
        db.outputs.uri() = ros::master::getURI();

        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS1MasterDatabase::sInternalState<OgnROS1Master>(nodeObj);
        state.mInitialized = false;
    }

private:
    bool mInitialized = false;
};

REGISTER_OGN_NODE()
