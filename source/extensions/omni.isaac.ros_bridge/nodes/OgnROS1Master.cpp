// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define BOOST_BIND_GLOBAL_PLACEHOLDERS
#include "ros/ros.h"
#undef BOOST_BIND_GLOBAL_PLACEHOLDERS

#include <OgnROS1MasterDatabase.h>

class OgnROS1Master
{
public:
    static bool compute(OgnROS1MasterDatabase& db)
    {
        // Always make sure there is a valid ROS master, Reset if its not valid
        if (!ros::master::check())
        {
            db.outputs.status() = false;
            db.outputs.host() = "";
            db.outputs.port() = 0;
            db.outputs.uri() = "";
            return false;
        }
        db.outputs.status() = true;
        db.outputs.host() = ros::master::getHost();
        db.outputs.port() = ros::master::getPort();
        db.outputs.uri() = ros::master::getURI();

        return true;
    }
};

REGISTER_OGN_NODE()
