// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
#include <omni/usd/UtilsIncludes.h>
#include <omni/physx/ContactEvent.h>
// clang-format on

#include "ContactManager.h"


namespace omni
{
namespace isaac
{
namespace sensor
{
ContactManager::ContactManager()
{
    // mContactCallbackPtr = carb::events::createSubscriptionToPop(
    //     carb::getCachedInterface<omni::physx::IPhysx>()->getSimulationEventStreamV2().get(),
    //     [this](carb::events::IEvent* e) { onContactReport(e); }, 0, "Contact Sensor Manager Event Handler");
}

ContactManager::~ContactManager()
{
    mContactCallbackPtr = nullptr;
}

void ContactManager::resetSensors()
{
    for (auto& it : mContactRawMap)
    {
        it.second.resize(0);
    }
    mContactRaw.clear();
    mCurrentTime = 0.0f;
}

void ContactManager::processContact(const omni::physx::ContactEventHeader c,
                                    const omni::physx::ContactData* contactDataBuffer,
                                    uint32_t& data_idx)
{
    // CARB_LOG_INFO("onContactReport");
    switch (c.type)
    {
    case omni::physx::ContactEventType::Enum::eCONTACT_FOUND:
    case omni::physx::ContactEventType::Enum::eCONTACT_PERSIST:
    {
        // CARB_LOG_INFO("Contact Header");

        // pxr::SdfPath body0 = reinterpret_cast<const pxr::SdfPath&>(c.actor0);
        // pxr::SdfPath body1 = reinterpret_cast<const pxr::SdfPath&>(c.actor1);

        // CARB_LOG_INFO("Collision between: Body 0: %s Body 1: %s \n", (char*)body0.GetText(),
        // (char*)body1.GetText()); CARB_LOG_INFO("%s, %s", body0.GetText(), body1.GetText());
        CsRawData contact;
        contact.time = mCurrentTime;
        contact.dt = mCurrentDt;
        contact.body0 = c.actor0;
        contact.body1 = c.actor1;
        removeRawData(ContactPair(c.actor0, c.actor1));
        // CARB_LOG_INFO("Adding to contact Raw");
        for (uint32_t i = 0; i < c.numContactData; i++)
        {
            auto data = contactDataBuffer[i + data_idx];
            // CARB_LOG_INFO("Contact Data");
            contact.normal = data.normal;
            contact.position = data.position;
            contact.impulse = data.impulse;
            mContactRaw.push_back(contact);
        }
        data_idx += c.numContactData;
        break;
    }
    case omni::physx::ContactEventType::Enum::eCONTACT_LOST:
    {
        // search for contact on persistent data
        // CARB_LOG_INFO("Contact Lost");

        removeRawData(ContactPair(c.actor0, c.actor1));
        break;
    }
    }
}

CsRawData* ContactManager::getCsRawData(const char* usdPath, size_t& size)
{
    pxr::SdfPath path(usdPath);
    return getCsRawData(asInt(path), size);
}

CsRawData* ContactManager::getCsRawData(uint64_t token, size_t& size)
{
    // If filtered list was not generated, create it now
    if (mContactRawMap.find(token) == mContactRawMap.end() || mContactRawMap[token].size() == 0)
    {
        mContactRawMap[token].resize(mContactRaw.size());
        auto it = std::copy_if(mContactRaw.begin(), mContactRaw.end(), mContactRawMap[token].begin(),
                               [token](const CsRawData& i) { return i.body0 == token || i.body1 == token; });
        mContactRawMap[token].resize(std::distance(mContactRawMap[token].begin(), it));
    }
    size = mContactRawMap[token].size();
    return mContactRawMap[token].data();
}

void ContactManager::removeRawData(const ContactPair& p)
{
    // CARB_LOG_INFO("Remove Raw Data %s %s", std::string(p.body0).c_str(), std::string(p.body1).c_str());
    if (mContactRawMap.find(p.body0) != mContactRawMap.end())
        mContactRawMap[p.body0].resize(0);
    if (mContactRawMap.find(p.body1) != mContactRawMap.end())
        mContactRawMap[p.body1].resize(0);
    if (mContactRaw.size() > 0)
    {
        auto it = std::remove_if(
            mContactRaw.begin(), mContactRaw.end(), [p](const CsRawData& d) { return p == ContactPair(d); });
        mContactRaw.erase(it, mContactRaw.end());
    }
}

void ContactManager::onPhysicsStep(const float& currentTime, const float& timeElapsed)
{
    CARB_PROFILE_ZONE(0, "Contact Sensor manager - physics step");
    mCurrentTime = currentTime;
    mCurrentDt = timeElapsed;

    const omni::physx::ContactEventHeader* contactEventHeadersBuffer = nullptr;
    const omni::physx::ContactData* contactDataBuffer = nullptr;
    const ::omni::physx::FrictionAnchor* frictionAnchorData = nullptr;
    uint32_t numContactData = 0;
    uint32_t numContactHeaders = 0;
    uint32_t numFrictionAnchorData = 0;
    {
        CARB_PROFILE_ZONE(0, "Contact Sensor manager - Get Data");
        numContactHeaders = carb::getCachedInterface<omni::physx::IPhysxSimulation>()->getFullContactReport(
            &contactEventHeadersBuffer, &contactDataBuffer, numContactData, &frictionAnchorData, numFrictionAnchorData);
    }
    uint32_t data_idx = 0;
    {
        CARB_PROFILE_ZONE(0, "Contact Sensor manager - update lists");
        for (uint32_t i = 0; i < numContactHeaders; i++)
        {
            const omni::physx::ContactEventHeader c = contactEventHeadersBuffer[i];
            processContact(c, contactDataBuffer, data_idx);
        }
        // CARB_LOG_WARN("Num Contacts: %ld - %ld",numContactHeaders, numContactData);
    }
}

float ContactManager::getCurrentTime()
{
    return mCurrentTime;
}

}
}
}
