// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
// clang-format on

#include "RadarSensor.h"

#include <carb/InterfaceUtils.h>

#include <omni/isaac/utils/Conversions.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>

#include <iostream>

using namespace ::physx;
using namespace pxr;

namespace omni
{
namespace isaac
{
namespace range_sensor
{


RadarSensor::RadarSensor(omni::renderer::IDebugDraw* debugDrawPtr, omni::physx::IPhysx* physxPtr)
    : RangeSensorComponent(debugDrawPtr, physxPtr)
{
}

RadarSensor::~RadarSensor()
{
}

void RadarSensor::onStart()
{
    RangeSensorComponent::onStart();
}

void RadarSensor::onComponentChange()
{

    RangeSensorComponent::onComponentChange();

    const pxr::RangeSensorSchemaRadar& typedPrim = (pxr::RangeSensorSchemaRadar)mPrim;

    isaac::utils::safeGetAttribute(typedPrim.GetRotationRateAttr(), mRotationRate);
    isaac::utils::safeGetAttribute(typedPrim.GetYawOffsetAttr(), mYawOffset);
}


void RadarSensor::tick()
{
    if (!mPxScene)
    {
        CARB_LOG_ERROR("Physics Scene does not exist");
        return;
    }
}


}
}
}
