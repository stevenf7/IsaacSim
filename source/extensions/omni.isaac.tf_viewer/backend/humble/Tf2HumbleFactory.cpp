// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include "Tf2Humble.h"

std::shared_ptr<Ros2BufferCore> Tf2FactoryHumble::createBuffer()
{
    return std::make_shared<Ros2BufferCoreHumble>();
}

Tf2Factory* createFactory()
{
    return new Tf2FactoryHumble();
}
