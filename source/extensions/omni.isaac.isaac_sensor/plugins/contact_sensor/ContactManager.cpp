// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
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
// clang-format on

#include "ContactManager.h"


namespace omni
{
namespace isaac
{
namespace isaac_sensor
{
ContactManager::ContactManager()
{
    mContactCallbackPtr = carb::events::createSubscriptionToPop(
        carb::getCachedInterface<omni::physx::IPhysx>()->getSimulationEventStream().get(),
        [this](carb::events::IEvent* e) { onContactReport(e); }, 0, "Contact Sensor Manager Event Handler");
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

void ContactManager::onContactReport(carb::events::IEvent* e)
{
    // CARB_LOG_INFO("onContactReport");
    carb::dictionary::IDictionary* dict = carb::dictionary::getCachedDictionaryInterface();
    switch (e->type)
    {
    case omni::physx::eContactFound:
    case omni::physx::eContactPersists:
    {
        // CARB_LOG_INFO("Contact Header");
        auto actor0 = dict->getItem(e->payload, "actor0");
        auto actor1 = dict->getItem(e->payload, "actor1");
        pxr::SdfPath body0 =
            pxr::decodeSdfPath(dict->getAsInt(dict->getItem(actor0, "0")), dict->getAsInt(dict->getItem(actor0, "1")));
        pxr::SdfPath body1 =
            pxr::decodeSdfPath(dict->getAsInt(dict->getItem(actor1, "0")), dict->getAsInt(dict->getItem(actor1, "1")));

        // CARB_LOG_INFO("Collision between: Body 0: %s Body 1: %s \n", (char*)body0.GetText(),
        // (char*)body1.GetText()); CARB_LOG_INFO("%s, %s", body0.GetText(), body1.GetText());
        mContactsToProcess = (size_t)dict->getAsInt(dict->getItem(e->payload, "numContactData"));
        mContactsProcessed = 0;
        CsRawData contact;
        contact.time = mCurrentTime;
        contact.dt = mCurrentDt;
        contact.body0 = (char*)body0.GetText();
        contact.body1 = (char*)body1.GetText();
        removeRawData(ContactPair(body0, body1));
        // CARB_LOG_INFO("Adding to contact Raw");
        mContactRaw.push_back(contact); // Need to finish getting the data on next events
        break;
    }
    case omni::physx::eContactLost:
    {
        // search for contact on persistent data
        // CARB_LOG_INFO("Contact Lost");
        auto actor0 = dict->getItem(e->payload, "actor0");
        auto actor1 = dict->getItem(e->payload, "actor1");
        pxr::SdfPath body0 =
            pxr::decodeSdfPath(dict->getAsInt(dict->getItem(actor0, "0")), dict->getAsInt(dict->getItem(actor0, "1")));
        pxr::SdfPath body1 =
            pxr::decodeSdfPath(dict->getAsInt(dict->getItem(actor1, "0")), dict->getAsInt(dict->getItem(actor1, "1")));
        // CARB_LOG_INFO("Collision lost: Body 0: %s Body 1: %s \n", (char*)body0.GetText(),
        // (char*)body1.GetText());

        removeRawData(ContactPair(body0, body1));
        break;
    }
    case omni::physx::eContactData:
    {
        // CARB_LOG_INFO("Contact Data");
        mContactRaw.back().normal = dict->get<carb::Float3>(dict->getItem(e->payload, "normal"));
        dict->getAsFloatArray(dict->getItem(e->payload, "position"), &mContactRaw.back().position.x, 3);
        dict->getAsFloatArray(dict->getItem(e->payload, "impulse"), &mContactRaw.back().impulse.x, 3);

        // CARB_LOG_INFO("%f %f %f", mContactRaw.back().impulse.x, mContactRaw.back().impulse.y,
        // mContactRaw.back().impulse.z); // Call sensors contact manager;
        // TODO multi thread

        if (++mContactsProcessed < mContactsToProcess)
        {
            CsRawData contact;
            contact.time = mContactRaw.back().time;
            contact.body0 = mContactRaw.back().body0;
            contact.body1 = mContactRaw.back().body1;
            mContactRaw.push_back(contact);
            // CARB_LOG_WARN("Collision Data: Body 0: %s Body 1: %s \n",
            // mContactRaw.back().body0,mContactRaw.back().body1); CARB_LOG_WARN("time: %f \n",
            // mContactRaw.back().time);
        }
        break;
    }
    }
}

CsRawData* ContactManager::getCsRawData(const char* usdPath, size_t& size)
{
    pxr::SdfPath path(usdPath);
    const auto token = path.GetToken();
    return getCsRawData(token, size);
}

CsRawData* ContactManager::getCsRawData(const pxr::TfToken token, size_t& size)
{
    // If filtered list was not generated, create it now
    if (mContactRawMap.find(token) == mContactRawMap.end() || mContactRawMap[token].size() == 0)
    {
        mContactRawMap[token].resize(mContactRaw.size());
        auto it = std::copy_if(
            mContactRaw.begin(), mContactRaw.end(), mContactRawMap[token].begin(),
            [token](const CsRawData& i)
            { return pxr::SdfPath(i.body0).GetToken() == token || pxr::SdfPath(i.body1).GetToken() == token; });
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
    mCurrentTime = currentTime;
    mCurrentDt = timeElapsed;

    for (auto& d : mContactRaw)
    {
        d.time = currentTime;
        d.dt = timeElapsed;
    }
}

float ContactManager::getCurrentTime()
{
    return mCurrentTime;
}

}
}
}
