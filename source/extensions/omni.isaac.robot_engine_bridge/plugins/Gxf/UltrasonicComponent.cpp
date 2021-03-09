// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
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

#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <carb/Framework.h>
#include <carb/Types.h>
#include <vector>
#include <string>
#include <rangeSensorSchema/ultrasonicArray.h>

#include "../Core/GxfComponent.h"

#include "UltrasonicComponent.h"
#include <carb/logging/Log.h>
#include <carb/profiler/Profile.h>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{
namespace gxf_bridge
{
UltrasonicComponent::UltrasonicComponent() : GxfComponent()
{

    framework = carb::getFramework();
    if (!framework)
    {
        CARB_LOG_ERROR("*** Failed to get Carbonite framework\n");
        return;
    }

    mUltrasonicSensorInterface = framework->acquireInterface<omni::isaac::range_sensor::UltrasonicSensorInterface>();
    if (!mUltrasonicSensorInterface)
    {
        CARB_LOG_ERROR("Failed to acquire omni::isaac::range_sensor interface");
        return;
    }
}

UltrasonicComponent::~UltrasonicComponent()
{
    framework->releaseInterface(mUltrasonicSensorInterface);
}

void UltrasonicComponent::onStart()
{
    onComponentChange();
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
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

    pxr::SdfPathVector emitterTargets;
    ultrasonicPrim.GetEmitterPrimsRel().GetTargets(&emitterTargets);
    int numSensors = static_cast<int>(emitterTargets.size());

    // std::vector<float> data =
    // mUltrasonicSensorInterface->getEnvelopeArrayFlattened(mUltrasonicPath.GetString().c_str());

    int numBins = mUltrasonicSensorInterface->getNumBins(mUltrasonicPath.GetString().c_str());
    int numEmitters = mUltrasonicSensorInterface->getNumEmitters(mUltrasonicPath.GetString().c_str());
    if (numEmitters <= 0 || numBins <= 0)
    {
        return;
    }
    // CARB_LOG_ERROR("%d %d", numEmitters, numBins);
    // if (mAllocator.get())
    // {
    //     CARB_LOG_ERROR("CAN ALLOCATE: %d", mAllocator.get()->is_available(100));
    // }
    // else
    // {
    //     CARB_LOG_ERROR("mAllocator not valid");
    // }

    std::vector<std::vector<float>> data =
        mUltrasonicSensorInterface->getActiveEnvelopeArray(mUltrasonicPath.GetString().c_str());

    auto maybe_message = nvidia::isaac::CreateUssEnvelopesMessage(mContext, mAllocator, data.size(), numBins, numSensors);
    if (!maybe_message)
    {
        // return maybe_message.error();
        CARB_LOG_ERROR("could not create envelopes message, %d", maybe_message.error());
    }
    auto message = std::move(maybe_message.value());

    // // ::isaac::Fill(message.envelopes, 0.0f);


    // auto message = nvidia::gxf::Entity::New(mContext);
    // auto tensor = message.value().add<nvidia::gxf::Tensor>("tensor");
    // // if (!tensor)
    // // {
    // //     return ToResultCode(tensor);
    // // }
    // const nvidia::gxf::Shape shape{ numEmitters, numBins };
    // auto result = tensor.value()->reshape<float>(shape, nvidia::gxf::MemoryStorageType::kHost, mAllocator);


    for (size_t i = 0; i < data.size(); i++)
    {
        for (size_t j = 0; j < data[i].size(); j++)
        {
            message.envelopes(i, j) = data[i][j];
        }
    }


    float maxRange = 1.0f;
    if (ultrasonicPrim.GetMaxRangeAttr().HasValue())
    {
        ultrasonicPrim.GetMaxRangeAttr().Get(&maxRange);
    }

    float minRange = 0.0f;
    if (ultrasonicPrim.GetMinRangeAttr().HasValue())
    {
        ultrasonicPrim.GetMinRangeAttr().Get(&minRange);
    }
    float horizFov = 1.0f;
    if (ultrasonicPrim.GetHorizontalFovAttr().HasValue())
    {
        ultrasonicPrim.GetHorizontalFovAttr().Get(&horizFov);
    }


    auto emitter_info = mUltrasonicSensorInterface->getEmitterFiringInfo(mUltrasonicPath.GetString().c_str());
    auto receiver_info = mUltrasonicSensorInterface->getReceiverFiringInfo(mUltrasonicPath.GetString().c_str());

    // Fill in firing info
    for (size_t i = 0; i < emitter_info.size(); i++)
    {
        message.firing_info->emissions[i].sensor_id = emitter_info[i].x;
        message.firing_info->emissions[i].mode = emitter_info[i].y;
    }
    for (size_t i = 0; i < receiver_info.size(); i++)
    {
        message.firing_info->envelopes[i].sensor_id = receiver_info[i].x;
        message.firing_info->envelopes[i].mode = receiver_info[i].y;
    }
    // Fill in pose uid
    for (int i = 0; i < numSensors; i++)
    {
        const std::string path = emitterTargets[i].GetString();
        auto maybeUid = mPoseTreeMap->findFrame(path);
        if (!maybeUid)
        {
            CARB_LOG_WARN("Cannot find pose uid for emitter %s", path.c_str());
            message.pose_frame_uids[i]->uid = 0u;
        }
        else
        {
            message.pose_frame_uids[i]->uid = maybeUid.value();
        }
    }

    message.sensor_info->range_max = maxRange;
    message.sensor_info->range_min = minRange;
    message.sensor_info->bin_size = (maxRange - minRange) / float(numBins);
    message.sensor_info->horizontal_fov = horizFov * M_PI / 180.0;

    message.timestamp->acqtime = this->mTimeNanoSeconds + mComponentTimeOffsetNanoSeconds;
    message.timestamp->pubtime = ::isaac::NowCount();
    // CARB_LOG_ERROR("%f %f %f", message.sensor_info->range_max, message.sensor_info->range_min,
    // message.sensor_info->bin_size);

    publish(mOutputComponent, mScanChannelName, std::move(message.entity));
}
void UltrasonicComponent::onComponentChange()
{
    // CARB_LOG_ERROR("UltrasonicComponent Update");
    GxfComponent::onComponentChange();

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
}
