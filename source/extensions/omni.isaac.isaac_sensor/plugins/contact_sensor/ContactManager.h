// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/events/EventsUtils.h>
#include <carb/logging/Log.h>

#include <omni/isaac/isaac_sensor/IsaacSensorTypes.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <omni/usd/UsdContext.h>
#include <physicsSchemaTools/UsdTools.h>
#include <physxSchema/physxContactReportAPI.h>
#include <usdPhysics/scene.h>

#include <PxActor.h>
#include <PxArticulationLink.h>
#include <PxRigidDynamic.h>
#include <PxScene.h>
#include <map>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace omni
{
namespace isaac
{
namespace isaac_sensor
{

struct ContactPair
{
    pxr::TfToken body0;
    pxr::TfToken body1;

    ContactPair(pxr::TfToken b0, pxr::TfToken b1) : body0(b0), body1(b1)
    {
        // keep body zero always the token with the smaller value
        if (b0 > b1)
        {
            body0 = b1;
            body1 = b0;
        }
    }
    ContactPair(pxr::SdfPath b0, pxr::SdfPath b1) : ContactPair(b0.GetToken(), b1.GetToken())
    {
    }
    ContactPair(CsRawData d) : ContactPair(pxr::SdfPath(d.body0), pxr::SdfPath(d.body1))
    {
    }

    bool operator==(ContactPair rhs) const
    {
        return body0 == rhs.body0 && body1 == rhs.body1;
    }
};

class ContactManager
{
public:
    ContactManager();

    virtual ~ContactManager();

    void resetSensors();

    void onContactReport(carb::events::IEvent* e);

    CsRawData* getCsRawData(const char* usdPath, size_t& size);

    CsRawData* getCsRawData(const pxr::TfToken token, size_t& size);

    void removeRawData(const ContactPair& p);

    void onPhysicsStep(const float& currentTime, const float& timeElapsed);

    float getCurrentTime();

private:
    std::vector<CsRawData> mContactRaw;
    std::map<pxr::TfToken, std::vector<CsRawData>> mContactRawMap;
    carb::events::ISubscriptionPtr mContactCallbackPtr;
    size_t mContactsToProcess{ 0 };
    size_t mContactsProcessed{ 0 };
    float mCurrentTime{ 0.0f };
    float mCurrentDt{ 0.0f };
};
}
}
}
