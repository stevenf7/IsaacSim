// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once


#include "../core/RangeSensorComponent.h"

#include <extensions/PxSceneQueryExt.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <pxr/base/gf/vec3f.h>
#include <pxr/usd/usd/inherits.h>
#include <rangeSensorSchema/radar.h>

#include <vector>

namespace omni
{
namespace isaac
{
namespace range_sensor
{

class RadarSensor : public RangeSensorComponent
{

public:
    RadarSensor(omni::physx::IPhysx* physxPtr, carb::fastcache::FastCache* fastCachePtr);
    ~RadarSensor();

    virtual void onStart();
    virtual void tick();
    virtual void onComponentChange();


private:
};


}
}
}
