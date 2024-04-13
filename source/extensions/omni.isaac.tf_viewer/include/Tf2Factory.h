// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <memory>
#include <string>
#include <vector>


class Ros2BufferCore
{
public:
    virtual bool setTransform(void* msg, const std::string& authority, bool isStatic) = 0;
    virtual bool getTransform(const std::string& targetFrame,
                              const std::string& sourceFrame,
                              double translation[],
                              double rotation[]) = 0;
    virtual bool getParentFrame(const std::string& frame, std::string& parentFrame) = 0;
    virtual std::vector<std::string> getFrames() = 0;
    virtual void clear() = 0;
};

class Tf2Factory
{
public:
    virtual ~Tf2Factory() = default;
    virtual std::shared_ptr<Ros2BufferCore> createBuffer() = 0;
};
