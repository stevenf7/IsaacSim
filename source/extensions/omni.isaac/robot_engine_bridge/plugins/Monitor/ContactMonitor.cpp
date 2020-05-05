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
#include <PhysxSchema/physxContactReportAPI.h>


#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

namespace omni
{
namespace isaac
{

using omni::isaac::dynamic_control::DcHandle;
using omni::isaac::dynamic_control::DcObjectType;
using omni::isaac::dynamic_control::DcTransform;
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
    IsaacMessage<isaac_message::Collision> collisionMessage;
    auto collisionProto = collisionMessage.initProto();

    carb::dictionary::IDictionary* dict = carb::dictionary::getCachedDictionaryInterface();

    if (e->type == carb::physics::eContactFound)
    {
        // printf("Contact Found %s %s\n", dict->get<const char*>(e->payload, "actor0"),
        //        dict->get<const char*>(e->payload, "actor1"));

        pxr::SdfPath thisPath(dict->get<const char*>(e->payload, "actor0"));

        // This report is for some other prim, skip
        if (thisPath != mTargetPrim.GetPath())
        {
            // printf("%s != %s\n", dict->get<const char*>(e->payload, "actor0"),
            // mTargetPrim.GetPath().GetString().c_str());
            return;
        }
        pxr::SdfPath otherPath(dict->get<const char*>(e->payload, "actor1"));

        // check if otherPath is in Ignored list
        for (pxr::SdfPath ignoredPath : mIgnoredTargets)
        {
            // this path matches an ignored once, skip contact event
            if (otherPath == ignoredPath)
            {
                // printf("otherPath == ignoredPath\n");
                return;
            }
        }
        collisionProto.setThisName(thisPath.GetString());
        collisionProto.setOtherName(otherPath.GetString());
        auto velProto = collisionProto.initVelocity();

        auto thisPoseProto = collisionProto.initThisPose();
        auto thisTranslationProto = thisPoseProto.initTranslation();
        auto thisRotationProto = thisPoseProto.initRotation();
        pxr::GfVec3d thisVel(0, 0, 0);

        DcObjectType prim_type = mDynamicControlPtr->peekObjectType(thisPath.GetString().c_str());
        if (prim_type == omni::isaac::dynamic_control::eDcObjectArticulation)
        {
            DcHandle artculationHandle = mDynamicControlPtr->getArticulation(thisPath.GetString().c_str());
            DcHandle artRootBody = mDynamicControlPtr->getArticulationRootBody(artculationHandle);
            DcTransform artPose = mDynamicControlPtr->getRigidBodyPose(artRootBody);
            thisVel = asGfVec3d(mDynamicControlPtr->getRigidBodyLinearVelocity(artRootBody)) * mUnitScale;

            toVector3dProto(asGfVec3d(artPose.p) * mUnitScale, thisTranslationProto);
            toSO3dProto(asGfQuatd(artPose.r), thisRotationProto);
        }
        else if (prim_type == omni::isaac::dynamic_control::eDcObjectRigidBody)
        {
            DcHandle rigidBodyHandle = mDynamicControlPtr->getRigidBody(thisPath.GetString().c_str());
            DcTransform rigidBodyPose = mDynamicControlPtr->getRigidBodyPose(rigidBodyHandle);

            toVector3dProto(asGfVec3d(rigidBodyPose.p) * mUnitScale, thisTranslationProto);
            toSO3dProto(asGfQuatd(rigidBodyPose.r), thisRotationProto);
            thisVel = asGfVec3d(mDynamicControlPtr->getRigidBodyLinearVelocity(rigidBodyHandle)) * mUnitScale;
        }
        else if (prim_type == omni::isaac::dynamic_control::eDcObjectNone)
        {
            // Calculate pose
            const pxr::GfTransform usdBodyPose(omni::usd::UsdUtils::getWorldTransformMatrix(mTargetPrim));
            pxr::GfVec3d usdBodyTranslation = usdBodyPose.GetTranslation();
            pxr::GfQuatd usdBodyRotation = usdBodyPose.GetRotation().GetQuat();
            // Set linear, angular velocity and acceleration to 0
            toVector3dProto(usdBodyTranslation * mUnitScale, thisTranslationProto);
            toSO3dProto(usdBodyRotation, thisRotationProto);
        }


        auto otherPoseProto = collisionProto.initOtherPose();
        auto otherTranslationProto = otherPoseProto.initTranslation();
        auto otherRotationProto = otherPoseProto.initRotation();
        pxr::GfVec3d otherVel(0, 0, 0);

        prim_type = mDynamicControlPtr->peekObjectType(otherPath.GetString().c_str());
        if (prim_type == omni::isaac::dynamic_control::eDcObjectArticulation)
        {
            DcHandle artculationHandle = mDynamicControlPtr->getArticulation(otherPath.GetString().c_str());
            DcHandle artRootBody = mDynamicControlPtr->getArticulationRootBody(artculationHandle);
            DcTransform artPose = mDynamicControlPtr->getRigidBodyPose(artRootBody);
            otherVel = asGfVec3d(mDynamicControlPtr->getRigidBodyLinearVelocity(artRootBody)) * mUnitScale;

            toVector3dProto(asGfVec3d(artPose.p) * mUnitScale, otherTranslationProto);
            toSO3dProto(asGfQuatd(artPose.r), otherRotationProto);
        }
        else if (prim_type == omni::isaac::dynamic_control::eDcObjectRigidBody)
        {
            DcHandle rigidBodyHandle = mDynamicControlPtr->getRigidBody(otherPath.GetString().c_str());
            DcTransform rigidBodyPose = mDynamicControlPtr->getRigidBodyPose(rigidBodyHandle);

            toVector3dProto(asGfVec3d(rigidBodyPose.p) * mUnitScale, otherTranslationProto);
            toSO3dProto(asGfQuatd(rigidBodyPose.r), otherRotationProto);
            otherVel = asGfVec3d(mDynamicControlPtr->getRigidBodyLinearVelocity(rigidBodyHandle)) * mUnitScale;
        }
        else if (prim_type == omni::isaac::dynamic_control::eDcObjectNone)
        {
            // Calculate pose
            const pxr::GfTransform usdBodyPose(
                omni::usd::UsdUtils::getWorldTransformMatrix(mStage->GetPrimAtPath(otherPath)));
            pxr::GfVec3d usdBodyTranslation = usdBodyPose.GetTranslation();
            pxr::GfQuatd usdBodyRotation = usdBodyPose.GetRotation().GetQuat();
            // Set linear, angular velocity and acceleration to 0
            toVector3dProto(usdBodyTranslation * mUnitScale, otherTranslationProto);
            toSO3dProto(usdBodyRotation, otherRotationProto);
        }
        // TODO: check which body we want velociy relative to
        toVector3dProto((thisVel - otherVel) * mUnitScale, velProto);

        // if we have contact data, also publish it
        if (e->type == carb::physics::eContactData)
        {
            auto normalProto = collisionProto.initContactNormal();
            normalProto.setX(dict->get<float>(e->payload, "normalX"));
            normalProto.setY(dict->get<float>(e->payload, "normalY"));
            normalProto.setZ(dict->get<float>(e->payload, "normalZ"));

            auto pointProto = collisionProto.initContactPoint();
            pointProto.setX(dict->get<float>(e->payload, "positionX") * mUnitScale);
            pointProto.setY(dict->get<float>(e->payload, "positionY") * mUnitScale);
            pointProto.setZ(dict->get<float>(e->payload, "positionZ") * mUnitScale);
        }
        std::vector<std::vector<uint8_t>> buffers;

        // printf("JSON: %s\n", isaac_message::gJsonCodec.encode(collisionProto).cStr());
        publish(mOutputComponent, mOutputChannel, collisionProto, isaac_message::RigidBody3GroupProtoId, buffers);
    }
}


void ContactMonitor::tick()
{
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
    if (!contactReportAPI.GetPhysxContactReportThresholdAttr())
    {
        contactReportAPI.CreatePhysxContactReportThresholdAttr();
    }
    if (!contactReportAPI.GetPhysxContactReportReportPairsRel())
    {
        contactReportAPI.CreatePhysxContactReportReportPairsRel();
    }

    contactReportAPI.GetPhysxContactReportThresholdAttr().Set(mForceThreshold);

    // const pxr::UsdRelationship rel = contactReportAPI.GetPhysxContactReportReportPairsRel();
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
            carb::getCachedInterface<carb::physics::PhysX>()->getSimulationEventStream().get(),
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
