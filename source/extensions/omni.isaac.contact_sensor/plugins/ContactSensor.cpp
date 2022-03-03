// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
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
// clang-format on

#include "ContactSensor.h"

#include <omni/kit/IStageUpdate.h>

// #include <omni/isaac/contact_sensor/ContactSensor.h>
#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/events/EventsUtils.h>
#include <carb/logging/Log.h>

#include <omni/kit/IStageUpdate.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <omni/physx/IPhysxSimulation.h>
#include <omni/usd/UsdContext.h>
#include <physicsSchemaTools/UsdTools.h>
#include <physxSchema/physxContactReportAPI.h>

#include <PxActor.h>
#include <PxArticulationLink.h>
#include <PxRigidDynamic.h>
#include <map>
#include <string>
#include <vector>


// pxr::SdfPath decodeSdfPath(const uint32_t ePart0, const uint32_t ePart1)
// {
//     const uint64_t part0 = uint64_t(ePart0);
//     const uint64_t part1 = uint64_t(ePart1);
//     const uint64_t uintPath = part0 + (part1 << 32);
//     return *((pxr::SdfPath*)&uintPath);
// }

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.contact_sensor.plugin", "Isaac Contact Sensor", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::contact_sensor::ContactSensorInterface)
CARB_PLUGIN_IMPL_DEPS(omni::physx::IPhysx, omni::physx::IPhysxSceneQuery, omni::kit::IStageUpdate)

using namespace pxr;

// static pxr::UsdStageWeakPtr gStage = nullptr;
static omni::physx::IPhysx* gPhysXInterface = nullptr;
static omni::isaac::contact_sensor::ContactManager* gContactManager = nullptr;
static omni::kit::IStageUpdate* gStageUpdate = nullptr;
static omni::kit::StageUpdateNode* gStageUpdateNode = nullptr;

namespace omni
{
namespace isaac
{
namespace contact_sensor
{
// assumes second arg is a format string literal
#define CS_LOG(level, fmt, ...)                                                                                        \
    {                                                                                                                  \
        CARB_LOG(level, fmt, ##__VA_ARGS__);                                                                           \
    }

// these assume the first arg is a format string literal
#define CS_LOG_VERBOSE(fmt, ...) CS_LOG(carb::logging::kLevelVerbose, fmt, ##__VA_ARGS__)
#define CS_LOG_INFO(fmt, ...) CS_LOG(carb::logging::kLevelInfo, fmt, ##__VA_ARGS__)
#define CS_LOG_WARN(fmt, ...) CS_LOG(carb::logging::kLevelWarn, fmt, ##__VA_ARGS__)
#define CS_LOG_ERROR(fmt, ...) CS_LOG(carb::logging::kLevelError, fmt, ##__VA_ARGS__)
#define CS_LOG_FATAL(fmt, ...) CS_LOG(carb::logging::kLevelFatal, fmt, ##__VA_ARGS__)


inline const pxr::SdfPath& intToPath(const uint64_t& path)
{
    static_assert(sizeof(pxr::SdfPath) == sizeof(uint64_t), "Change to make the same size as pxr::SdfPath");

    return reinterpret_cast<const pxr::SdfPath&>(path);
}

void OnContactReport(const omni::physx::ContactEventHeader* eventHeaders,
                     uint32_t numEventHeaders,
                     const omni::physx::ContactData* contactData,
                     uint32_t numContactData,
                     void* userData)
{
    ContactManager* contactManager = reinterpret_cast<ContactManager*>(userData);
    size_t processedContactData = 0;
    for (uint32_t i = 0; i < numEventHeaders; i++)
    {
        const omni::physx::ContactEventHeader& header = eventHeaders[i];
        // contactReportData->mContactHeaders.back().contactDataOffset =
        // uint32_t(contactReportData->mContactData.size()); for (uint32_t j = 0; j < header.numContactData; j++)
        // {
        //     CARB_ASSERT(header.contactDataOffset + j < numContactData);
        //     contactReportData->mContactData.push_back(contactData[header.contactDataOffset + j]);
        // }

        switch (header.type)
        {
        case omni::physx::ContactEventType::eCONTACT_FOUND:
        case omni::physx::ContactEventType::eCONTACT_PERSIST:
        {
            // CS_LOG_INFO("Contact Header");
            auto actor0 = header.actor0;
            auto actor1 = header.actor1;
            pxr::SdfPath body0 = intToPath(actor0);
            pxr::SdfPath body1 = intToPath(actor1);
            // CS_LOG_INFO("%s, %s", body0.GetText(), body1.GetText());
            size_t mContactsToProcess = (size_t)header.numContactData;
            CsRawData contact;
            contact.dt = contactManager->getDt();
            contact.time = contactManager->getCurrentTime();
            contact.body0 = (char*)body0.GetText();
            contact.body1 = (char*)body1.GetText();
            contactManager->removeRawData(ContactPair(body0, body1));

            for (size_t j = 0; j < mContactsToProcess; j++)
            {
                // CS_LOG_INFO("Contact Data");
                auto& c = contactData[processedContactData++];
                contact.normal = c.normal;
                contact.position = c.position;
                contact.impulse = c.impulse;

                // CS_LOG_INFO("%f %f %f", mContactRaw.back().impulse.x, mContactRaw.back().impulse.y,
                // mContactRaw.back().impulse.z); Call sensors contact manager;
                // TODO multi thread
                // CS_LOG_INFO("Body paths");


                contactManager->rawDataPushBack(contact);
            }
            break;
        }
        case omni::physx::ContactEventType::eCONTACT_LOST:
        {
            // search for contact on persistent data
            // CS_LOG_INFO("Contact Lost");
            auto actor0 = header.actor0;
            auto actor1 = header.actor1;
            pxr::SdfPath body0 = intToPath(actor0);
            pxr::SdfPath body1 = intToPath(actor1);
            // CS_LOG_INFO("%s, %s", body0.GetText(), body1.GetText());
            contactManager->removeRawData(ContactPair(body0, body1));
            break;
        }
        }
    }
    contactManager->processAllRaw();
}


inline float lerp(const float& start, const float& end, const float t)
{
    return start + ((end - start) * t);
}

ContactSensor::ContactSensor(pxr::TfToken body) : bodyID(body)
{
    reset();
}

void ContactManager::processAllRaw()
{
    for (auto& it : mSensorHandleMap)
    {
        it.second.update(mCurrentTime);
        if (!it.second.processedRaw())
        {
            size_t size;
            auto contacts = getCsRawData(it.second.getBody(), size);
            it.second.processRawContacts(contacts, size);
        }
    }
    mSensorsProcessed = false;
}


void ContactSensor::initialize(CsProperties props)
{
    mProps = props;
}

void ContactSensor::reset()
{
    mCurrentTime = 0.0f;
    mCurrent = 0;
    mReadingPair[0] = mReadingPair[1] = CsReading();
    // mProcessedRaw = true;
    mProcessedReadings = false;
    mSensorReadings.clear();
}

void ContactSensor::processRawContacts(CsRawData* rawContact, const size_t& size)
{
    // CS_LOG_INFO("Processing Raw Contacts %ld", size);
    // First, get the sensor global pose;
    mReadingPair[mCurrent].value = 0.0f;
    mReadingPair[mCurrent].inContact = false;
    if (size > 0)
    {

        pxr::SdfPath actor(rawContact[0].body0);
        if (actor.GetToken() != bodyID) // If Parent is on index 1
            actor = pxr::SdfPath(rawContact[0].body1);
        // CS_LOG_INFO("getting PxActor");
        pxr::GfTransform parentPose;
        pxr::GfVec3d pose(mProps.position.x, mProps.position.y, mProps.position.z);
        ::physx::PxActor* pxActor =
            (::physx::PxActor*)gPhysXInterface->getPhysXPtr(actor, omni::physx::PhysXType::ePTActor);
        // CS_LOG_INFO("used Physx interface");
        if (pxActor)
        {
            // CS_LOG_INFO("Found PxActor");
            ::physx::PxRigidActor* rd = (::physx::PxRigidActor*)pxActor;
            ::physx::PxTransform _pose = rd->getGlobalPose();
            parentPose.SetTranslation(pxr::GfVec3d(_pose.p.x, _pose.p.y, _pose.p.z));
            parentPose.SetRotation(
                pxr::GfRotation(pxr::GfQuatd(_pose.q.w, pxr::GfVec3d(_pose.q.x, _pose.q.y, _pose.q.z))));
            // CS_LOG_INFO("Parent Pose: %f %f %f", _pose.p.x, _pose.p.y, _pose.p.z);
        }
        else
        {
            // CS_LOG_INFO("PxLink");
            ::physx::PxArticulationLink* link =
                (::physx::PxArticulationLink*)gPhysXInterface->getPhysXPtr(actor, omni::physx::PhysXType::ePTLink);
            ::physx::PxTransform _pose = link->getGlobalPose();
            parentPose.SetTranslation(pxr::GfVec3d(_pose.p.x, _pose.p.y, _pose.p.z));
            parentPose.SetRotation(
                pxr::GfRotation(pxr::GfQuatd(_pose.q.w, pxr::GfVec3d(_pose.q.x, _pose.q.y, _pose.q.z))));
            // CS_LOG_INFO("Parent Pose: %f %f %f", _pose.p.x, _pose.p.y, _pose.p.z);
        }

        pose = parentPose.GetMatrix().Transform(pose);
        pxr::GfVec3d totalImpulse(0.0, 0.0, 0.0);
        for (size_t i = 0; i < size; ++i)
        {
            pxr::GfVec3d contactPoint(rawContact[i].position.x, rawContact[i].position.y, rawContact[i].position.z);
            // CS_LOG_INFO("contact Pose: %f %f %f", contactPoint[0], contactPoint[1], contactPoint[2]);
            // CS_LOG_INFO("sensor Pose: %f %f %f", pose[0],pose[1], pose[2]);
            auto distance = pose - contactPoint;
            // CS_LOG_INFO("Distance: %lf %lf", distance.GetLength(), pose.GetLength());
            // Check if distance from sensor to contact position is within sensor radius
            if (mProps.radius < 0 || distance.GetLength() < mProps.radius)
            {
                mReadingPair[mCurrent].inContact = mReadingPair[mCurrent].inContact || true;
                // compute force from impulse (F = i/dt) and add to sensor output
                totalImpulse += pxr::GfVec3d(rawContact[i].impulse.x, rawContact[i].impulse.y, rawContact[i].impulse.z);
                // CS_LOG_INFO(
                // "contact sensor value: %d, %f, %lf", mCurrent, mReadingPair[mCurrent].value,
                // pxr::GfVec3d(rawContact[i].impulse.x, rawContact[i].impulse.y, rawContact[i].impulse.z).GetLength());
            }
        }
        mReadingPair[mCurrent].value =
            std::min((float)(totalImpulse.GetLength() / rawContact[0].dt), mProps.maxThreshold);
    }
    // CS_LOG_INFO("Done Processing Raw");
    mProcessedRaw = true;
}

void ContactSensor::update(float time)
{
    // CS_LOG_INFO("Sensor Update %f", time);
    mCurrent ^= 1;
    mReadingPair[mCurrent].time = time;
    mReadingPair[mCurrent].value = mReadingPair[!mCurrent].value;
    mReadingPair[mCurrent].inContact = mReadingPair[!mCurrent].inContact;
    mProcessedReadings = false;
}

size_t ContactSensor::getNumReadings()
{
    if (!mProcessedReadings)
    {
        size_t size;
        getSensorReadings(size);
    }
    return mSensorReadings.size();
}

CsReading* ContactSensor::getSensorReadings(size_t& num_readings)
{
    if (mProps.sensorPeriod > 0)
    {
        if (!mProcessedReadings)
        {
            float start = mReadingPair[!mCurrent].time;
            float end = mReadingPair[mCurrent].time;
            mSensorReadings.clear();
            while (mCurrentTime < end)
            {
                if (mCurrentTime >= start)
                {
                    float time_pos = (mCurrentTime - start) / (end - start);
                    CsReading reading;
                    reading.time = mCurrentTime;
                    reading.value = lerp(mReadingPair[!mCurrent].value, mReadingPair[mCurrent].value, time_pos);
                    if (reading.value < mProps.minThreshold)
                    {
                        reading.value = 0.0f;
                    }
                    reading.inContact = reading.value > 0.0f;
                    mSensorReadings.push_back(reading);
                }
                mCurrentTime += mProps.sensorPeriod;
            }
            mProcessedReadings = true;
        }
    }
    else
    {
        mSensorReadings.clear();
        mSensorReadings.push_back(mReadingPair[mCurrent]);
        if (mSensorReadings.back().value < mProps.minThreshold)
        {
            mSensorReadings.back().value = 0.0f;
            mSensorReadings.back().inContact = false;
        }
    }
    num_readings = mSensorReadings.size();
    // CS_LOG_INFO("Num Readings :%ld", num_readings);
    return mSensorReadings.data();
}


void onPhysicsUpdate(omni::physx::SimulationStatusEvent eventStatus, void* userData)
{
    // cast manager back to
    // ContactManager* contactManager = (ContactManager*)userData;
    if (eventStatus == omni::physx::SimulationStatusEvent::eSimulationStarting)
    {
        // CS_LOG_INFO("Simulation starting");
        // contactManager->resetSensors();
    }
    if (eventStatus == omni::physx::SimulationStatusEvent::eSimulationEnded)
    {
        // CS_LOG_INFO("Simulation Ended");
        // contactManager->resetSensors();
    }
}

void onPhysicsStep(float timeElapsed, void* userData)
{
    // cast manager back, and call its step handler
    ContactManager* contactManager = (ContactManager*)userData;
    contactManager->onPhysicsStep(timeElapsed);
}

static void onAttach(long int stageId, double metersPerUnit, void* userData)
{
}

static void onDetach(void* userData)
{
    // cast manager back
    ContactManager* contactManager = reinterpret_cast<ContactManager*>(userData);
    contactManager->clearAllSensors();
}

static void onStop(void* userData)
{
    // cast manager back
    ContactManager* contactManager = reinterpret_cast<ContactManager*>(userData);
    contactManager->resetSensors();
}

static void onPrimRemove(const pxr::SdfPath& primPath, void* userData)
{
    ContactManager* contactManager = reinterpret_cast<ContactManager*>(userData);
    contactManager->removeAllSensorsFromBody(primPath.GetText());
}

void ContactManager::removeAllSensorsFromBody(const char* usdPath)
{
    pxr::SdfPath path(usdPath);
    const auto& it = mPrimSensorMap.find(path.GetToken());
    if (it != mPrimSensorMap.end())
    {
        for (auto cshandle : it->second)
        {
            mSensorHandleMap.erase(cshandle);
        }
        mPrimSensorMap.erase(it);
    }
}
ContactManager::ContactManager(omni::physx::IPhysx* physxInterface)
{
    // setup the physx simulation and contact callbacks
    mStepSubscription = physxInterface->subscribePhysicsStepEvents(omni::isaac::contact_sensor::onPhysicsStep, this);
    mEventSubscription = physxInterface->subscribePhysicsSimulationEvents(onPhysicsUpdate, this);

    mContactCallbackId = carb::getCachedInterface<omni::physx::IPhysxSimulation>()->subscribePhysicsContactReportEvents(
        &OnContactReport, this);

    // mStageCallbackPtr = carb::events::createSubscriptionToPop()
}

void ContactManager::unSubscribeEvents(omni::physx::IPhysx* physxInterface)
{
    physxInterface->unsubscribePhysicsStepEvents(mStepSubscription);
    physxInterface->unsubscribePhysicsSimulationEvents(mEventSubscription);
    carb::getCachedInterface<omni::physx::IPhysxSimulation>()->unsubscribePhysicsContactReportEvents(mContactCallbackId);
}

void ContactManager::onPhysicsStep(float timeElapsed)
{
    // mContactRawMap.clear(); //Clear filtered raw map
    mCurrentTime += timeElapsed;
    mCurrentDt = timeElapsed;
    // CS_LOG_INFO("Update %f, %f", mCurrentTime, timeElapsed)
    for (auto& d : mContactRaw)
    {
        d.time = mCurrentTime;
        d.dt = timeElapsed;
    }
    processAllRaw();
    mSensorsProcessed = false;
}

void ContactManager::resetSensors()
{
    // CS_LOG_INFO("Reset Sensors")
    for (auto& it : mSensorHandleMap)
    {
        it.second.reset();
    }
    for (auto& it : mContactRawMap)
    {
        it.second.resize(0);
    }
    mContactRaw.clear();
    mCurrentTime = 0.0f;
}

// void ContactManager::onContactReport(carb::events::IEvent* e)

CsHandle ContactManager::addSensor(const char* usdPath, CsProperties props)
{
    pxr::SdfPath path(usdPath);
    // We may want to ensure prim at path has the ContactAPI. It won't break if there's no contact API, but no report
    // will be generated.
    auto stage = omni::usd::UsdContext::getContext()->getStage();
    // CS_LOG_INFO("Adding sensor on %s", usdPath);
    auto targetPrim = stage->GetPrimAtPath(path);
    if (targetPrim)
    {
        // CS_LOG_INFO("Prim Found");
        pxr::PhysxSchemaPhysxContactReportAPI contactReportAPI = pxr::PhysxSchemaPhysxContactReportAPI::Get(stage, path);

        if (!contactReportAPI)
        {
            contactReportAPI = pxr::PhysxSchemaPhysxContactReportAPI::Apply(targetPrim);
        }
        if (!contactReportAPI.GetThresholdAttr())
        {
            contactReportAPI.CreateThresholdAttr();
        }
        if (!contactReportAPI.GetReportPairsRel())
        {
            contactReportAPI.CreateReportPairsRel();
        }

        contactReportAPI.GetThresholdAttr().Set(props.minThreshold);
        // Add sensor in the list
        CsHandle newSensorHandle = ++mNextId;
        mSensorHandleMap[newSensorHandle] = ContactSensor(path.GetToken());
        mSensorHandleMap[newSensorHandle].initialize(props);
        mPrimSensorMap[path.GetToken()].push_back(newSensorHandle);
        return newSensorHandle;
    }

    return kCsInvalidHandle;
}

CsHandle* ContactManager::getSensorsOnBody(const char* usdPath, size_t& num_sensors)
{
    pxr::SdfPath path(usdPath);
    if (mPrimSensorMap.find(path.GetToken()) != mPrimSensorMap.end())
    {
        num_sensors = mPrimSensorMap[path.GetToken()].size();
        return mPrimSensorMap[path.GetToken()].data();
    }
    return nullptr;
}

bool ContactManager::removeSensor(CsHandle sensor)
{
    if (mSensorHandleMap.find(sensor) != mSensorHandleMap.end())
    {
        mPrimSensorMap[mSensorHandleMap[sensor].getBody()].erase(
            std::remove(mPrimSensorMap[mSensorHandleMap[sensor].getBody()].begin(),
                        mPrimSensorMap[mSensorHandleMap[sensor].getBody()].end(), sensor));
        mSensorHandleMap.erase(sensor);
        return true;
    }
    return false;
}

CsReading* ContactManager::getSensorReadings(CsHandle sensor, size_t& num_readings)
{
    // CS_LOG_INFO("Get Sensor Readings %ld", sensor);
    if (mSensorHandleMap.find(sensor) != mSensorHandleMap.end())
    {
        // CS_LOG_INFO("Sensor Found");
        // If sensor was not processed
        if (!mSensorHandleMap[sensor].processedRaw())
        {
            // CS_LOG_INFO("Sensor not processed");
            size_t size;
            auto contacts = getCsRawData(mSensorHandleMap[sensor].getBody(), size);
            // CS_LOG_INFO("body contacts size: %ld", size);
            mSensorHandleMap[sensor].processRawContacts(contacts, size);
        }
        return mSensorHandleMap[sensor].getSensorReadings(num_readings);
    }
    num_readings = 0;
    return nullptr;
}

CsReading ContactManager::getSensorSimReading(CsHandle sensor)
{
    if (mSensorHandleMap.find(sensor) != mSensorHandleMap.end())
    {
        if (!mSensorHandleMap[sensor].processedRaw())
        {
            // CS_LOG_INFO("Sensor not processed");
            size_t size;
            auto contacts = getCsRawData(mSensorHandleMap[sensor].getBody(), size);
            // CS_LOG_INFO("body contacts size: %ld", size);
            mSensorHandleMap[sensor].processRawContacts(contacts, size);
        }
        return mSensorHandleMap[sensor].getSimReading();
    }
    return CsReading();
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
    // CS_LOG_INFO("Get Contact Raw Data");
    if (mContactRawMap.find(token) == mContactRawMap.end() || mContactRawMap[token].size() == 0)
    {
        // CS_LOG_INFO("Get Contact Raw map not initialized");
        mContactRawMap[token].resize(mContactRaw.size());
        auto it = std::copy_if(
            mContactRaw.begin(), mContactRaw.end(), mContactRawMap[token].begin(),
            [token](const CsRawData& i)
            { return pxr::SdfPath(i.body0).GetToken() == token || pxr::SdfPath(i.body1).GetToken() == token; });
        mContactRawMap[token].resize(std::distance(mContactRawMap[token].begin(), it));
        // CS_LOG_INFO("Copied data from raw to map");
    }

    size = mContactRawMap[token].size();
    return mContactRawMap[token].data();
}

void ContactManager::removeRawData(const ContactPair p)
{
    // CS_LOG_INFO("Remove Raw Data %s %s", std::string(p.body0).c_str(), std::string(p.body1).c_str());
    // CS_LOG_INFO("  Clean Sensor Map");
    if (mPrimSensorMap.find(p.body0) != mPrimSensorMap.end())
    {

        for (CsHandle it : mPrimSensorMap[p.body0])
        {
            mSensorHandleMap[it].clearRawProcessFlag();
        }
    }
    if (mPrimSensorMap.find(p.body1) != mPrimSensorMap.end())
    {
        for (CsHandle it : mPrimSensorMap[p.body1])
        {
            mSensorHandleMap[it].clearRawProcessFlag();
        }
    }
    // CS_LOG_INFO("  Clean contact Map");
    if (mContactRawMap.find(p.body0) != mContactRawMap.end())
        mContactRawMap[p.body0].resize(0);
    if (mContactRawMap.find(p.body1) != mContactRawMap.end())
        mContactRawMap[p.body1].resize(0);
    // CS_LOG_INFO("  Clean contact Raw");
    if (mContactRaw.size() > 0)
    {
        auto it = std::remove_if(
            mContactRaw.begin(), mContactRaw.end(), [p](const CsRawData& d) { return p == ContactPair(d); });
        mContactRaw.erase(it, mContactRaw.end());
    }
    // CS_LOG_INFO("  Raw Size: %ld", mContactRaw.size());
}

void ContactManager::clearAllSensors()
{
    mPrimSensorMap.clear();
    mSensorHandleMap.clear();
    mContactRaw.clear();
    mContactRawMap.clear();
}


}
}
}

CARB_EXPORT void carbOnPluginStartup()
{
    using namespace omni::isaac::contact_sensor;

    carb::Framework* framework = carb::getFramework();
    if (!framework)
    {
        CS_LOG_ERROR("Failed to get Carbonite framework");
        return;
    }

    gPhysXInterface = framework->acquireInterface<omni::physx::IPhysx>();
    if (!gPhysXInterface)
    {
        CS_LOG_ERROR("Failed to acquire PhysX` interface");
        return;
    }

    gContactManager = new ContactManager(gPhysXInterface);

    if (gStageUpdate == nullptr)
    {
        gStageUpdate = framework->acquireInterface<omni::kit::IStageUpdate>();
        if (gStageUpdate != nullptr)
        {
            omni::kit::StageUpdateNodeDesc desc = { 0 };
            desc.displayName = "ContactManager";
            desc.userData = gContactManager;
            desc.onAttach = onAttach;
            desc.onDetach = onDetach;
            desc.onPrimRemove = onPrimRemove;
            desc.onStop = onStop;

            gStageUpdateNode = gStageUpdate->createStageUpdateNode(desc);
            if (gStageUpdateNode == nullptr)
            {
                framework->releaseInterface(gStageUpdate);
                gStageUpdate = nullptr;
            }
        }
    }
}

CARB_EXPORT void carbOnPluginShutdown()
{
    if (gContactManager)
    {
        if (gPhysXInterface)
            gContactManager->unSubscribeEvents(gPhysXInterface);
        delete gContactManager;
        gContactManager = nullptr;
    }
    if (gPhysXInterface)
    {
        carb::Framework* framework = carb::getFramework();
        if (framework)
        {
            framework->releaseInterface(gPhysXInterface);
        }
    }
    if (gStageUpdate != nullptr)
    {
        if (gStageUpdateNode != nullptr)
        {
            gStageUpdate->destroyStageUpdateNode(gStageUpdateNode);
            gStageUpdateNode = nullptr;
        }
        carb::Framework* framework = carb::getFramework();
        if (framework)
        {
            framework->releaseInterface(gStageUpdate);
        }
        gStageUpdate = nullptr;
    }
}

using namespace omni::isaac::contact_sensor;

CARB_EXPORT size_t CsGetNumSensorsOnBody(const char* usdPath)
{
    size_t num_sensors = 0;
    if (gContactManager)
    {
        gContactManager->getSensorsOnBody(usdPath, num_sensors);
    }
    return num_sensors;
}

CARB_EXPORT CsHandle* CsGetSensorsOnBody(const char* usdPath, size_t& num_sensors)
{
    CsHandle* sensors = nullptr;
    num_sensors = 0;
    if (gContactManager)
    {
        sensors = gContactManager->getSensorsOnBody(usdPath, num_sensors);
    }

    return sensors;
}

CARB_EXPORT CsRawData* CsGetBodyCsRawData(const char* usdPath, size_t& num_contacts)
{
    CsRawData* data = nullptr;
    num_contacts = 0;
    if (gContactManager)
    {
        data = gContactManager->getCsRawData(usdPath, num_contacts);
    }
    return data;
}

CARB_EXPORT size_t CsGetSensorReadingsSize(const CsHandle sensor)
{
    size_t num_readings = 0;
    if (gContactManager)
    {
        gContactManager->getSensorReadings(sensor, num_readings);
    }
    return num_readings;
}

CARB_EXPORT CsReading* CsGetSensorReadings(const CsHandle sensor, size_t& num_readings)
{
    num_readings = 0;
    CsReading* data = nullptr;
    if (gContactManager)
    {
        data = gContactManager->getSensorReadings(sensor, num_readings);
    }
    return data;
}


CARB_EXPORT CsReading CsGetSensorSimReading(const CsHandle sensor)
{
    CsReading data;
    if (gContactManager)
    {
        data = gContactManager->getSensorSimReading(sensor);
    }
    return data;
}

CARB_EXPORT CsHandle CsAddSensorOnBody(const char* usdPath, const CsProperties props)
{
    CsHandle handle = kCsInvalidHandle;
    if (gContactManager)
    {
        handle = gContactManager->addSensor(usdPath, props);
        // CS_LOG_INFO("Added Contact sensor %ld", handle);
    }
    return handle;
}

CARB_EXPORT bool CsRemoveSensor(CsHandle sensor)
{
    if (gContactManager)
    {
        return gContactManager->removeSensor(sensor);
    }
    return false;
}

void fillInterface(omni::isaac::contact_sensor::ContactSensorInterface& iface)
{
    using namespace omni::isaac::contact_sensor;

    memset(&iface, 0, sizeof(iface));

    iface.getNumSensorsOnBody = CsGetNumSensorsOnBody;
    iface.getSensorsOnBody = CsGetSensorsOnBody;

    iface.getBodyCsRawData = CsGetBodyCsRawData;

    iface.getSensorReadingsSize = CsGetSensorReadingsSize;
    iface.getSensorReadings = CsGetSensorReadings;
    iface.getSensorSimReading = CsGetSensorSimReading;

    iface.addSensorOnBody = CsAddSensorOnBody;
    iface.removeSensor = CsRemoveSensor;
}
