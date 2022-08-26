// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "UltrasonicComponent.h"

#include "../Core/IsaacComponent.h"

#include <carb/Framework.h>
#include <carb/InterfaceUtils.h>
#include <carb/Types.h>
#include <carb/logging/Log.h>
#include <carb/profiler/Profile.h>

#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <rangeSensorSchema/ultrasonicArray.h>

#include <string>
#include <vector>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

UltrasonicComponent::UltrasonicComponent() : IsaacComponent()
{

    mUltrasonicSensorInterface = carb::getCachedInterface<omni::isaac::range_sensor::UltrasonicSensorInterface>();
    if (!mUltrasonicSensorInterface)
    {
        CARB_LOG_ERROR("Failed to acquire omni::isaac::range_sensor interface");
        return;
    }
}

UltrasonicComponent::~UltrasonicComponent()
{
}

void UltrasonicComponent::onStart()
{
    onComponentChange();
    mSkipFirstFrame = true;
}
void UltrasonicComponent::tick()
{
}

void UltrasonicComponent::publishAllMessages()
{
    if (mSkipFirstFrame)
    {
        mSkipFirstFrame = false;
        return;
    }
    CARB_PROFILE_ZONE(0, "REB UltrasonicComponent Tick");

    pxr::UsdPrim prim = mStage->GetPrimAtPath(mUltrasonicPath);
    if (!prim.IsA<pxr::RangeSensorSchemaUltrasonicArray>())
    {
        CARB_LOG_ERROR("Prim is not a USS Prim");
        return;
    }
    pxr::RangeSensorSchemaUltrasonicArray ultrasonicPrim = pxr::RangeSensorSchemaUltrasonicArray(prim);
    if (!mUltrasonicSensorInterface->isUSS(mUltrasonicPath.GetString().c_str()))
    {
        CARB_LOG_ERROR("Prim is not registered with USS extension");
        return;
    }

    std::vector<float> data = mUltrasonicSensorInterface->getEnvelopeArrayFlattened(mUltrasonicPath.GetString().c_str());
    int numBins = mUltrasonicSensorInterface->getNumBins(mUltrasonicPath.GetString().c_str());
    int numEmitters = mUltrasonicSensorInterface->getNumEmitters(mUltrasonicPath.GetString().c_str());
    if (numEmitters <= 0 || numBins <= 0)
    {
        return;
    }


    // scanMessageProto.setTheta(kj::ArrayPtr<const float>(theta, theta + numColsTicked));
    // scanMessageProto.setPhi(kj::ArrayPtr<const float>(phi, phi + numRows));
    IsaacMessage<isaac_message::Tensor> tensorMessage;
    auto tensorProto = tensorMessage.initProto();
    tensorProto.setElementType(ElementType::FLOAT32);
    tensorProto.initSizes(2);
    tensorProto.setSizes({ numEmitters, numBins });
    tensorProto.setScanlineStride(0);
    tensorProto.setDataBufferIndex(0);


    std::vector<std::unique_ptr<IsaacBuffer>> buffers(1);
    buffers[0] = std::make_unique<IsaacHostBuffer>(numEmitters * numBins * sizeof(float));
    std::memcpy(buffers[0]->data(), data.data(), numEmitters * numBins * sizeof(float));
    publish(mOutputComponent, mScanChannelName, tensorMessage, buffers);
}
void UltrasonicComponent::onComponentChange()
{
    // CARB_LOG_ERROR("UltrasonicComponent Update");
    IsaacComponent::onComponentChange();

    const pxr::RobotEngineBridgeSchemaRobotEngineUltrasonic& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEngineUltrasonic)mPrim;
    isaac::utils::safeGetAttribute(typedPrim.GetOutputComponentAttr(), mOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputChannelAttr(), mScanChannelName);

    pxr::SdfPathVector targets;
    typedPrim.GetUltrasonicPrimRel().GetTargets(&targets);

    if (targets.size() == 0)
    {
        return;
    }
    mUltrasonicPath = targets[0];
}
}
}
}
