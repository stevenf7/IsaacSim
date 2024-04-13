// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include "Tf2Foxy.h"

std::shared_ptr<Ros2BufferCore> Tf2FactoryFoxy::createBuffer()
{
    return std::make_shared<Ros2BufferCoreFoxy>();
}

Tf2Factory* createFactory()
{
    return new Tf2FactoryFoxy();
}
