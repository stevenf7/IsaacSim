// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <include/Tf2Factory.h>

namespace isaacsim
{
namespace ros2
{
namespace tf_viewer
{

class Tf2FactoryImpl : public Tf2Factory
{
public:
    virtual std::shared_ptr<Ros2BufferCore> createBuffer();
};

} // namespace tf_viewer
} // namespace ros2
} // namespace isaacsim

#ifdef _MSC_VER
extern "C" __declspec(dllexport) isaacsim::ros2::tf_viewer::Tf2Factory* createFactory();
#else
extern "C" isaacsim::ros2::tf_viewer::Tf2Factory* createFactory();
#endif
