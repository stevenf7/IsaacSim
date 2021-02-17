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
#include <string>

#include "ContactMonitor.h"
#include "../Utils/IsaacConversions.h"
#include <omni/isaac/utils/Conversions.h>
// #include <boost/algorithm/string.hpp>
#include <carb/Framework.h>
#include <carb/logging/Log.h>
#include <carb/InterfaceUtils.h>
#include <carb/events/EventsUtils.h>
#include <carb/filesystem/IFileSystem.h>
#include <physxSchema/physxContactReportAPI.h>


#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

namespace omni
{
namespace isaac
{

using omni::isaac::dynamic_control::DcHandle;
using omni::isaac::dynamic_control::DcObjectType;
using omni::isaac::dynamic_control::DcTransform;
using utils::conversions::asDcTransform;
using utils::conversions::asGfQuatd;
using utils::conversions::asGfVec3d;

namespace robot_engine_bridge
{


ContactMonitor::ContactMonitor(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
}

ContactMonitor::~ContactMonitor()
{
    mContactCallback = nullptr;
}

void ContactMonitor::processContact(carb::events::IEvent* e)
{
    carb::dictionary::IDictionary* dict = carb::dictionary::getCachedDictionaryInterface();

    if (e->type == omni::physx::SimulationEvent::eContactFound)
    {
        // printf("Contact Found %s %s\n", dict->get<const char*>(e->payload, "actor0"),
        //        dict->get<const char*>(e->payload, "actor1"));

        pxr::SdfPath thisPath(dict->get<const char*>(e->payload, "actor0"));
        pxr::SdfPath otherPath(dict->get<const char*>(e->payload, "actor1"));

        // This report is for some other prim, skip
        if (thisPath != mTargetPrim.GetPath() && otherPath != mTargetPrim.GetPath())
        {
            // printf("%s != %s\n", dict->get<const char*>(e->payload, "actor0"),
            // mTargetPrim.GetPath().GetString().c_str());
            return;
        }


        // check if otherPath is in Ignored list
        for (pxr::SdfPath ignoredPath : mIgnoredTargets)
        {
            // this path matches an ignored once, skip contact event
            if (otherPath == ignoredPath || thisPath == ignoredPath)
            {
                // printf("otherPath == ignoredPath\n");
                return;
            }
        }
        ContactData contact;


        contact.thisName = thisPath.GetString();
        contact.otherName = otherPath.GetString();
        pxr::GfVec3d thisVel(0, 0, 0);

        DcObjectType prim_type = mDynamicControlPtr->peekObjectType(thisPath.GetString().c_str());
        if (prim_type == omni::isaac::dynamic_control::eDcObjectArticulation)
        {
            DcHandle artculationHandle = mDynamicControlPtr->getArticulation(thisPath.GetString().c_str());
            DcHandle artRootBody = mDynamicControlPtr->getArticulationRootBody(artculationHandle);
            DcTransform artPose = mDynamicControlPtr->getRigidBodyPose(artRootBody);
            thisVel = asGfVec3d(mDynamicControlPtr->getRigidBodyLinearVelocity(artRootBody)) * mUnitScale;
            contact.thisPose = artPose;
        }
        else if (prim_type == omni::isaac::dynamic_control::eDcObjectRigidBody)
        {
            DcHandle rigidBodyHandle = mDynamicControlPtr->getRigidBody(thisPath.GetString().c_str());
            DcTransform rigidBodyPose = mDynamicControlPtr->getRigidBodyPose(rigidBodyHandle);

            contact.thisPose = rigidBodyPose;

            thisVel = asGfVec3d(mDynamicControlPtr->getRigidBodyLinearVelocity(rigidBodyHandle)) * mUnitScale;
        }
        else if (prim_type == omni::isaac::dynamic_control::eDcObjectNone)
        {
            // Calculate pose
            const pxr::GfTransform usdBodyPose(omni::usd::UsdUtils::getWorldTransformMatrix(mTargetPrim));
            pxr::GfVec3d usdBodyTranslation = usdBodyPose.GetTranslation();
            pxr::GfQuatd usdBodyRotation = usdBodyPose.GetRotation().GetQuat();

            contact.thisPose = asDcTransform(usdBodyTranslation, usdBodyRotation);
        }

        pxr::GfVec3d otherVel(0, 0, 0);

        prim_type = mDynamicControlPtr->peekObjectType(otherPath.GetString().c_str());
        if (prim_type == omni::isaac::dynamic_control::eDcObjectArticulation)
        {
            DcHandle artculationHandle = mDynamicControlPtr->getArticulation(otherPath.GetString().c_str());
            DcHandle artRootBody = mDynamicControlPtr->getArticulationRootBody(artculationHandle);
            DcTransform artPose = mDynamicControlPtr->getRigidBodyPose(artRootBody);
            otherVel = asGfVec3d(mDynamicControlPtr->getRigidBodyLinearVelocity(artRootBody)) * mUnitScale;

            contact.otherPose = artPose;
        }
        else if (prim_type == omni::isaac::dynamic_control::eDcObjectRigidBody)
        {
            DcHandle rigidBodyHandle = mDynamicControlPtr->getRigidBody(otherPath.GetString().c_str());
            DcTransform rigidBodyPose = mDynamicControlPtr->getRigidBodyPose(rigidBodyHandle);
            contact.otherPose = rigidBodyPose;
            otherVel = asGfVec3d(mDynamicControlPtr->getRigidBodyLinearVelocity(rigidBodyHandle)) * mUnitScale;
        }
        else if (prim_type == omni::isaac::dynamic_control::eDcObjectNone)
        {
            // Calculate pose
            const pxr::GfTransform usdBodyPose(
                omni::usd::UsdUtils::getWorldTransformMatrix(mStage->GetPrimAtPath(otherPath)));
            pxr::GfVec3d usdBodyTranslation = usdBodyPose.GetTranslation();
            pxr::GfQuatd usdBodyRotation = usdBodyPose.GetRotation().GetQuat();
            contact.otherPose = asDcTransform(usdBodyTranslation, usdBodyRotation);
        }
        contact.velocity = utils::conversions::asCarbFloat3((thisVel - otherVel) * mUnitScale);


        // if we have contact data, also publish it
        if (e->type == omni::physx::SimulationEvent::eContactData)
        {

            contact.normal.x = dict->get<float>(e->payload, "normalX");
            contact.normal.y = dict->get<float>(e->payload, "normalY");
            contact.normal.z = dict->get<float>(e->payload, "normalZ");

            contact.position.x = dict->get<float>(e->payload, "positionX") * mUnitScale;
            contact.position.y = dict->get<float>(e->payload, "positionY") * mUnitScale;
            contact.position.z = dict->get<float>(e->payload, "positionZ") * mUnitScale;
        }
        mContactData.push_back(contact);
    }
}


void ContactMonitor::tick()
{
}

void ContactMonitor::publishAllMessages()
{
    for (auto& contact : mContactData)
    {
        IsaacMessage<isaac_message::Collision> collisionMessage;
        auto collisionProto = collisionMessage.initProto();

        collisionProto.setThisName(contact.thisName);
        collisionProto.setOtherName(contact.otherName);
        auto velProto = collisionProto.initVelocity();

        auto thisPoseProto = collisionProto.initThisPose();
        auto thisTranslationProto = thisPoseProto.initTranslation();
        auto thisRotationProto = thisPoseProto.initRotation();
        pxr::GfVec3d thisVel(0, 0, 0);


        toVector3dProto(asGfVec3d(contact.thisPose.p) * mUnitScale, thisTranslationProto);
        toSO3dProto(asGfQuatd(contact.thisPose.r), thisRotationProto);


        auto otherPoseProto = collisionProto.initOtherPose();
        auto otherTranslationProto = otherPoseProto.initTranslation();
        auto otherRotationProto = otherPoseProto.initRotation();
        pxr::GfVec3d otherVel(0, 0, 0);


        toVector3dProto(asGfVec3d(contact.otherPose.p) * mUnitScale, otherTranslationProto);
        toSO3dProto(asGfQuatd(contact.otherPose.r), otherRotationProto);

        // TODO: check which body we want velociy relative to
        toVector3dProto(contact.velocity, velProto);

        // auto normalProto = collisionProto.initContactNormal();
        // toVector3dProto(contact.normal, normalProto);
        // auto pointProto = collisionProto.initContactPoint();
        // toVector3dProto(contact.velocity, pointProto);

        std::vector<std::unique_ptr<IsaacBuffer>> buffers;

        // printf("JSON: %s\n", isaac_message::gJsonCodec.encode(collisionProto).cStr());
        publish(mOutputComponent, mOutputChannel, collisionMessage, buffers);
    }
    mContactData.clear();
}

void ContactMonitor::onStart()
{
    onComponentChange();
}

void ContactMonitor::onComponentChange()
{
    IsaacComponent::onComponentChange();

    const pxr::RobotEngineBridgeSchemaRobotEngineContactMonitor& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEngineContactMonitor)mPrim;


    isaac::utils::safeGetAttribute(typedPrim.GetOutputComponentAttr(), mOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputChannelAttr(), mOutputChannel);

    isaac::utils::safeGetAttribute(typedPrim.GetForceThresholdAttr(), mForceThreshold);

    pxr::SdfPathVector targets;
    typedPrim.GetTargetPrimRel().GetTargets(&targets);
    typedPrim.GetIgnoredPrimsRel().GetTargets(&mIgnoredTargets);
    if (targets.size() == 0)
    {
        CARB_LOG_ERROR("No Target Prim Specified");
        return;
    }

    mTargetPrim = mStage->GetPrimAtPath(targets[0]);

    if (!mTargetPrim)
    {
        CARB_LOG_ERROR("%s target path not found\n", targets[0].GetString().c_str());
        return;
    }
    pxr::PhysxSchemaPhysxContactReportAPI contactReportAPI =
        pxr::PhysxSchemaPhysxContactReportAPI::Get(mStage, targets[0]);

    if (!contactReportAPI)
    {
        contactReportAPI = pxr::PhysxSchemaPhysxContactReportAPI::Apply(mTargetPrim);
    }
    if (!contactReportAPI.GetThresholdAttr())
    {
        contactReportAPI.CreateThresholdAttr();
    }
    if (!contactReportAPI.GetReportPairsRel())
    {
        contactReportAPI.CreateReportPairsRel();
    }

    contactReportAPI.GetThresholdAttr().Set(mForceThreshold);

    // const pxr::UsdRelationship rel = contactReportAPI.GetReportPairsRel();
    // if (rel)
    // {
    //     typedPrim.GetIgnoredPrimsRel().GetTargets(&mIgnoredTargets);
    //     if (mIgnoredTargets.size() > 0)
    //     {
    //         rel.SetTargets(mIgnoredTargets);
    //     }
    // }

    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);

    if (this->mEnabled)
    {
        mContactCallback = carb::events::createSubscriptionToPop(
            carb::getCachedInterface<omni::physx::IPhysx>()->getSimulationEventStream().get(),
            [this](carb::events::IEvent* e) { processContact(e); }, 0, "Robot Engine ContactMonitor");
    }
    else
    {
        mContactCallback = nullptr;
    }
}

}
}
}
