// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <carb/PluginUtils.h>

#include <geometry_msgs/msg/transform_stamped.h>
#include <include/Tf2FactoryFoxy.h>
#include <tf2/buffer_core.h>
#include <tf2_msgs/msg/tf_message.h>

class Ros2BufferCoreFoxy : public Ros2BufferCore
{
public:
    Ros2BufferCoreFoxy();
    virtual ~Ros2BufferCoreFoxy();
    virtual bool setTransform(void* msg, const std::string& authority, bool isStatic);
    virtual bool getTransform(const std::string& targetFrame,
                              const std::string& sourceFrame,
                              double translation[],
                              double rotation[]);
    virtual bool getParentFrame(const std::string& frame, std::string& parentFrame);
    virtual std::vector<std::string> getFrames();
    virtual void clear();

private:
    tf2::BufferCore mBuffer;
    std::vector<std::string> mFrames;
};
