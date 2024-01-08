// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
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

#include <omni/kit/IStageUpdate.h>
#include <omni/physx/ContactEvent.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <omni/physx/IPhysxSimulation.h>
#include <omni/usd/UsdContext.h>
#include <physicsSchemaTools/UsdTools.h>
#include <physxSchema/physxContactReportAPI.h>
#include <pxr/usd/usdPhysics/scene.h>

#include <IsaacSensorTypes.h>
#include <PxActor.h>

#if defined(_WIN32)
#    include <PxArticulationLink.h>
#else
#    pragma GCC diagnostic push
#    pragma GCC diagnostic ignored "-Wpragmas"
#    include <PxArticulationLink.h>
#    pragma GCC diagnostic pop
#endif

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
namespace sensor
{


// asInt() is the same as SdfPath::_AsInt()
// asInt(a)==asInt(b) <=> a is same path as b,
// which is how SdfPath::operator== is currently defined.
// If USD changes sizeof(pxr::SdfPath), we will need to change
inline uint64_t asInt(const pxr::SdfPath& path)
{
    static_assert(sizeof(pxr::SdfPath) == sizeof(uint64_t), "Change to make the same size as pxr::SdfPath");
    uint64_t ret;
    std::memcpy(&ret, &path, sizeof(pxr::SdfPath));
    return ret;
}
struct ContactPair
{
    uint64_t body0;
    uint64_t body1;

    ContactPair(uint64_t b0, uint64_t b1) : body0(b0), body1(b1)
    {
        // keep body zero always the token with the smaller value
        if (b0 > b1)
        {
            body0 = b1;
            body1 = b0;
        }
    }
    ContactPair(pxr::SdfPath b0, pxr::SdfPath b1) : ContactPair(asInt(b0), asInt(b1))
    {
    }
    ContactPair(CsRawData d) : ContactPair(d.body0, d.body1)
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

    void processContact(const omni::physx::ContactEventHeader c,
                        const omni::physx::ContactData* contactDataBuffer,
                        uint32_t& data_idx);

    CsRawData* getCsRawData(const char* usdPath, size_t& size);

    CsRawData* getCsRawData(uint64_t token, size_t& size);

    void removeRawData(const ContactPair& p);

    void onPhysicsStep(const float& currentTime, const float& timeElapsed);

    float getCurrentTime();

private:
    std::vector<CsRawData> mContactRaw;
    std::map<uint64_t, std::vector<CsRawData>> mContactRawMap;
    carb::events::ISubscriptionPtr mContactCallbackPtr;
    size_t mContactsToProcess{ 0 };
    size_t mContactsProcessed{ 0 };
    float mCurrentTime{ 0.0f };
    float mCurrentDt{ 0.0f };
};
}
}
}
