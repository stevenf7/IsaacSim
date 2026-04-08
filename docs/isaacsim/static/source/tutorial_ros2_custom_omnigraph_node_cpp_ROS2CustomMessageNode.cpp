// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <ROS2CustomMessageNodeDatabase.h>
#include <string>

// In this example, we will publish a string message with an OmniGraph Node
#include "tutorial_interfaces/msg/sphere.h"

// ROS includes for creating nodes, publishers etc.
#include "rcl/rcl.h"

// Helpers to explicit shorten names you know you will use
using omni::graph::core::Type;
using omni::graph::core::BaseDataType;


class ROS2CustomMessageNode
{
public:
    static bool compute(ROS2CustomMessageNodeDatabase& db)
    {
        auto& state = db.internalState<ROS2CustomMessageNode>();

        if(!state.pub_created)
        {
            state.context = rcl_get_zero_initialized_context();
            state.init_options = rcl_get_zero_initialized_init_options();
            state.allocator = rcl_get_default_allocator();
            rcl_ret_t rc;
            // create init_options
            rc = rcl_init_options_init(&state.init_options, state.allocator);
            if (rc != RCL_RET_OK)
            {
                printf("Error rcl_init_options_init.\n");
                return false;
            }

            // create context
            rc = rcl_init(0, nullptr, &state.init_options, &state.context);
            if (rc != RCL_RET_OK)
            {
                printf("Error in rcl_init.\n");
                return false;
            }

            // create rcl_node
            state.my_node = rcl_get_zero_initialized_node();
            state.node_ops = rcl_node_get_default_options();
            rc = rcl_node_init(&state.my_node, "node_0", "custom_node", &state.context, &state.node_ops);
            if (rc != RCL_RET_OK)
            {
                printf("Error in rcl_node_init\n");
                return false;
            }

            const char * topic_name = "sphere_msg";

            const rosidl_message_type_support_t * my_type_support = ROSIDL_GET_MSG_TYPE_SUPPORT(tutorial_interfaces, msg, Sphere);

            state.pub_options = rcl_publisher_get_default_options();

            // Initialize Publisher
            rc = rcl_publisher_init(
                &state.my_pub,
                &state.my_node,
                my_type_support,
                topic_name,
                &state.pub_options);
            if (RCL_RET_OK != rc)
            {
                printf("Error in rcl_publisher_init %s.\n", topic_name);
                return false;
            }
            // Node, publisher was successfully created
            state.pub_created = true;

            return true;
        }

        tutorial_interfaces__msg__Sphere* ros_msg = tutorial_interfaces__msg__Sphere__create();

        // Set the center of the sphere with the input to the OG node
        ros_msg->center.x = db.inputs.publishCenter()[0];
        ros_msg->center.y = db.inputs.publishCenter()[1];
        ros_msg->center.z = db.inputs.publishCenter()[2];

        // Set the radius of the sphere to the input radius
        ros_msg->radius = db.inputs.publishRadius();

        rcl_ret_t rc;
        rc = rcl_publish(&state.my_pub, ros_msg, NULL);
        if (rc != RCL_RET_OK)
        {
            // RCL_RET_PUBLISHER_INVALID is returned initially and then the message gets published
            return false;
        }

        // Destroy the ROS message published to release the memory it used
        tutorial_interfaces__msg__Sphere__destroy(ros_msg);

        // Returning true tells Omnigraph that the compute was successful and the output value is now valid.
        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = ROS2CustomMessageNodeDatabase::sPerInstanceState<ROS2CustomMessageNode>(nodeObj, instanceId);


        // Remove Publisher
        rcl_ret_t rc = rcl_publisher_fini(&state.my_pub, &state.my_node);
        if (rc != RCL_RET_OK) {
            printf("Failed to finalize publisher: %d\n", rc);
        }

        // Remove Node
        rc = rcl_node_fini(&state.my_node);
        if (rc != RCL_RET_OK) {
            printf("Failed to finalize node: %d\n", rc);
        }

        state.pub_created = false;
    }

private:
    rcl_publisher_t my_pub;
    rcl_node_t my_node;
    rcl_context_t context;
    rcl_node_options_t node_ops;
    rcl_init_options_t init_options;
    rcl_allocator_t allocator;
    rcl_publisher_options_t pub_options;
    bool pub_created {false};

};

// This macro provides the information necessary to OmniGraph that lets it automatically register and deregister
// your node type definition.
REGISTER_OGN_NODE()
