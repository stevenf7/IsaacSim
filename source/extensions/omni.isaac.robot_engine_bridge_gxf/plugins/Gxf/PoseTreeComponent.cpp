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

#include "PoseTreeComponent.h"

#include "../Core/GxfComponent.h"
#include "../Utils/IsaacConversions.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/logging/Log.h>
#include <carb/profiler/Profile.h>

#include <omni/isaac/utils/Conversions.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>

#include <regex>
#include <string>
#include <vector>

namespace omni
{
namespace isaac
{

using utils::conversions::asGfQuatd;
using utils::conversions::asGfVec3d;


using omni::isaac::dynamic_control::DcHandle;
using omni::isaac::dynamic_control::DcObjectType;
using omni::isaac::dynamic_control::DcTransform;

namespace robot_engine_bridge_gxf
{

PoseTreeComponent::PoseTreeComponent(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : GxfComponent(), mDynamicControlPtr(dynamicControlPtr)
{


    mTimeline = carb::getCachedInterface<omni::timeline::ITimeline>();
}

PoseTreeComponent::~PoseTreeComponent()
{
}

void PoseTreeComponent::onStart()
{
    // CARB_LOG_ERROR("PoseTreeComponent Start");
    onComponentChange();
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
}

void PoseTreeComponent::tick()
{
    CARB_PROFILE_ZONE(0, "REB PoseTreeComponent Tick");

    if (!getAtlasFrontend())
    {
        return;
    }

    nvidia::isaac::PoseTree& poseTree = mAtlas->pose_tree();
    auto maybeUid = poseTree.findOrCreateFrame("sim");
    if (!maybeUid)
    {
        CARB_LOG_ERROR("Unable to create or find root pose frame sim");
        return;
    }
    mRootUid = maybeUid.value();

    // Loop over each prim
    for (size_t i = 0; i < mPrims.size(); i++)
    {
        pxr::UsdPrim prim = mStage->GetPrimAtPath(mPrims[i]);
        if (!prim)
        {
            CARB_LOG_WARN("prim %s does not exist", mPrims[i].GetString().c_str());
            continue;
        }
        addPrimToPoseTree(prim, mDepthLimits[i], mRootUid, poseTree, false);
    }
}

bool PoseTreeComponent::getAtlasFrontend()
{
    gxf_result_t result;
    gxf_uid_t atlas_eid;
    const std::string atlas_entity = getEntityName(mOutputComponent, mOutputChannel);
    if ((result = GxfEntityFind(mContext, atlas_entity.c_str(), &atlas_eid)))
    {
        CARB_LOG_ERROR("GxfEntityFind Atlas %s, %s", atlas_entity.c_str(), GxfResultStr(result));
        return false;
    }
    gxf_tid_t atlas_tid;
    if ((result = GxfComponentTypeId(mContext, nvidia::TypenameAsString<nvidia::isaac::AtlasFrontend>(), &atlas_tid)))
    {
        CARB_LOG_ERROR("GxfComponentTypeId AtlasFrontend %s", GxfResultStr(result));
        return false;
    }
    gxf_uid_t atlas_cid;
    const std::string frontend_component = getComponentName(mOutputComponent, mOutputChannel);
    if ((result = GxfComponentFind(mContext, atlas_eid, atlas_tid, frontend_component.c_str(), nullptr, &atlas_cid)))
    {
        CARB_LOG_ERROR("GxfComponentFind Atlas %s, %s", frontend_component.c_str(), GxfResultStr(result));
        return false;
    }
    auto atlas = nvidia::gxf::Handle<nvidia::isaac::AtlasFrontend>::Create(mContext, atlas_cid);
    mAtlas = std::move(atlas.value());

    return true;
}

void PoseTreeComponent::addPrimToPoseTree(const pxr::UsdPrim& prim,
                                          const int depth,
                                          const nvidia::isaac::PoseTree::frame_t parentUid,
                                          nvidia::isaac::PoseTree& poseTree,
                                          bool useLocalPose)
{
    const std::string path = prim.GetPath().GetString();

    nvidia::isaac::PoseTree::frame_t poseUid;
    if (mPrimRegexStr.empty() || std::regex_match(path, mPrimRegex))
    {
        auto maybeUid = mPoseTreeMap->findOrCreateNamedFrame(path, poseTree);
        if (!maybeUid)
        {
            CARB_LOG_ERROR("Unable to create prim %s named pose frame", path.c_str());
            return;
        }
        // CARB_LOG_WARN("Create named pose for prim %s", path.c_str());
        poseUid = maybeUid.value();
    }
    else
    {
        auto maybeUid = mPoseTreeMap->findOrCreateUnnamedFrame(path, poseTree);
        if (!maybeUid)
        {
            CARB_LOG_ERROR("Unable to create prim %s unnamed pose frame", path.c_str());
            return;
        }
        // CARB_LOG_WARN("Create named pose for prim %s", path.c_str());
        poseUid = maybeUid.value();
    }

    // Get pose of the prim
    ::isaac::Pose3d pose = ::isaac::Pose3d::Identity();
    omni::isaac::dynamic_control::DcObjectType prim_type =
        mDynamicControlPtr->peekObjectType(prim.GetPath().GetString().c_str());
    if (prim_type == omni::isaac::dynamic_control::eDcObjectArticulation)
    {
        DcHandle articulationHandle = mDynamicControlPtr->getArticulation(prim.GetPath().GetString().c_str());
        DcHandle artRootBody = mDynamicControlPtr->getArticulationRootBody(articulationHandle);
        // Calculate pose
        DcTransform articulationPose = mDynamicControlPtr->getRigidBodyPose(artRootBody);
        pxr::GfVec3d artTranslation = asGfVec3d(articulationPose.p);
        pxr::GfQuatd artRotation = asGfQuatd(articulationPose.r);

        // Converts to robot engine pose
        toVector3d(artTranslation * mUnitScale, pose.translation);
        toSO3d(artRotation, pose.rotation);
        useLocalPose = false;
    }
    else if (prim_type == omni::isaac::dynamic_control::eDcObjectRigidBody)
    {

        DcHandle rigidBodyHandle = mDynamicControlPtr->getRigidBody(prim.GetPath().GetString().c_str());
        // Calculate pose
        DcTransform rigidBodyPose = mDynamicControlPtr->getRigidBodyPose(rigidBodyHandle);
        pxr::GfVec3d rigidBodyTranslation = asGfVec3d(rigidBodyPose.p);
        pxr::GfQuatd rigidBodyRotation = asGfQuatd(rigidBodyPose.r);
        // Converts to robot engine pose
        toVector3d(rigidBodyTranslation * mUnitScale, pose.translation);
        toSO3d(rigidBodyRotation, pose.rotation);
        useLocalPose = false;
    }
    else if (prim_type == omni::isaac::dynamic_control::eDcObjectNone)
    {
        // Calculate pose

        pxr::UsdTimeCode primTimeCode = pxr::UsdTimeCode::Default();
        std::vector<double> times;
        pxr::UsdGeomXformable(prim).GetTimeSamples(&times);

        if (times.size() > 1)
        {
            primTimeCode = round(mTimeline->getCurrentTime() * this->mStage->GetTimeCodesPerSecond());
        }

        pxr::GfQuatd usdBodyRotation;
        pxr::GfVec3d usdBodyTranslation;
        if (useLocalPose)
        {
            const pxr::GfTransform usdBodyPose(omni::usd::UsdUtils::getLocalTransformMatrix(prim, primTimeCode));
            usdBodyTranslation = usdBodyPose.GetTranslation();
            usdBodyRotation = usdBodyPose.GetRotation().GetQuat();
        }
        else
        {
            const pxr::GfTransform usdBodyPose(omni::usd::UsdUtils::getWorldTransformMatrix(prim, primTimeCode));
            usdBodyTranslation = usdBodyPose.GetTranslation();
            usdBodyRotation = usdBodyPose.GetRotation().GetQuat();
        }
        // Converts to robot engine proto message
        toVector3d(usdBodyTranslation * mUnitScale, pose.translation);
        toSO3d(usdBodyRotation, pose.rotation);
    }

    if (useLocalPose)
    {
        // Set pose tree relative to parent prim
        const auto result = poseTree.set(parentUid, poseUid, this->mTimeSeconds, pose);
        if (!result)
        {
            CARB_LOG_ERROR("Unable to set pose for parent_T_%s", path.c_str());
            return;
        }
    }
    else
    {
        // Set pose tree relative to simulation root frame
        const auto result = poseTree.set(mRootUid, poseUid, this->mTimeSeconds, pose);
        if (!result)
        {
            CARB_LOG_ERROR("Unable to set pose for sim_T_%s", path.c_str());
            return;
        }
    }
    // CARB_LOG_WARN("Set pose for prim %s", path.c_str());

    if (depth == 0)
    {
        return;
    }

    // Add the current prim and its immediate descendants
    pxr::UsdPrimSiblingRange range = prim.GetChildren();
    for (pxr::UsdPrimSiblingRange::iterator iter = range.begin(); iter != range.end(); ++iter)
    {
        pxr::UsdPrim child_prim = *iter;
        addPrimToPoseTree(child_prim, depth - 1, poseUid, poseTree, true);
    }
}

void PoseTreeComponent::onComponentChange()
{
    // CARB_LOG_ERROR("PoseTreeComponent Update");
    GxfComponent::onComponentChange();

    const pxr::RobotEngineBridgeSchemaRobotEnginePoseTree& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEnginePoseTree)mPrim;
    isaac::utils::safeGetAttribute(typedPrim.GetOutputComponentAttr(), mOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputChannelAttr(), mOutputChannel);
    isaac::utils::safeGetAttribute(typedPrim.GetDepthLimitsAttr(), mDepthLimits);
    isaac::utils::safeGetAttribute(typedPrim.GetPrimRegexAttr(), mPrimRegexStr);

    CARB_LOG_WARN("PoseTree regex string %s", mPrimRegexStr.c_str());

    mPrimRegex = std::regex(mPrimRegex);

    typedPrim.GetPrimsRel().GetTargets(&mPrims);

    if (mPrims.size() != mDepthLimits.size())
    {
        CARB_LOG_ERROR("prims and depthLimits do not have same size");
        return;
    }
}
}
}
}
