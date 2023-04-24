// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// // clang-format off
// #include <UsdPCH.h>
// // clang-format on

// #include "PoseTreeComponent.h"

// #include "../Utils/IsaacConversions.h"
// #include "gems/pose_tree/pose_tree_operations.hpp"

// #include <carb/Framework.h>
// #include <carb/Types.h>
// #include <carb/logging/Log.h>
// #include <carb/profiler/Profile.h>

// #include <omni/isaac/utils/Conversions.h>
// #include <omni/usd/UsdUtils.h>
// #include <omni/usd/UtilsIncludes.h>

// #include <regex>
// #include <string>
// #include <vector>

// namespace omni
// {
// namespace isaac
// {

// using utils::conversions::asGfQuatd;
// using utils::conversions::asGfVec3d;


// using omni::isaac::dynamic_control::DcHandle;
// using omni::isaac::dynamic_control::DcObjectType;
// using omni::isaac::dynamic_control::DcTransform;

// namespace gxf_bridge
// {

// PoseTreeComponent::PoseTreeComponent(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
// mDynamicControlPtr(dynamicControlPtr)
// {


//     mTimeline = carb::getCachedInterface<omni::timeline::ITimeline>();
// }

// PoseTreeComponent::~PoseTreeComponent()
// {
// }

// void PoseTreeComponent::onStart()
// {
//     // CARB_LOG_ERROR("PoseTreeComponent Start");
//     onComponentChange();
//     mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
// }

// void PoseTreeComponent::tick()
// {
//     CARB_PROFILE_ZONE(0, "REB PoseTreeComponent Tick");

//     auto maybeUid = mPoseTreeMap->findOrCreateNamedFrame("sim");
//     if (!maybeUid)
//     {
//         CARB_LOG_ERROR("Unable to create or find root pose frame sim");
//         return;
//     }
//     mRootUid = maybeUid.value();

//     // Create new message
//     auto maybe_message = nvidia::gxf::Entity::New(mContext);
//     if (!maybe_message)
//     {
//         CARB_LOG_ERROR("Create pose tree message entity %s", GxfResultStr(maybe_message.error()));
//         return;
//     }
//     nvidia::gxf::Entity message = std::move(maybe_message.value());

//     // Add a timestamp to the message
//     auto maybe_timestamp = message.add<nvidia::gxf::Timestamp>();
//     if (!maybe_timestamp)
//     {
//         CARB_LOG_ERROR("Add timestamp to pose tree %s", GxfResultStr(maybe_timestamp.error()));
//         return;
//     }
//     const nvidia::gxf::Handle<nvidia::gxf::Timestamp> timestamp = maybe_timestamp.value();
//     timestamp->acqtime = this->mTimeNanoSeconds + mComponentTimeOffsetNanoSeconds;
//     timestamp->pubtime = ::isaac::NowCount();

//     mEdgeCount = 0;
//     // Loop over each prim
//     gxf_result_t edge_result;
//     for (size_t i = 0; i < mPrims.size(); i++)
//     {
//         pxr::UsdPrim prim = mStage->GetPrimAtPath(mPrims[i]);
//         if (!prim)
//         {
//             CARB_LOG_WARN("prim %s does not exist", mPrims[i].GetString().c_str());
//             continue;
//         }
//         if ((edge_result = addPrim(message, prim, mDepthLimits[i], mRootUid, false)))
//         {
//             CARB_LOG_ERROR("Add prim fails %s", GxfResultStr(edge_result));
//             return;
//         }
//     }

//     if (mEdgeCount == 0)
//     {
//         CARB_LOG_WARN("Pose Message contains no edge");
//         return;
//     }

//     // Activate the message
//     const auto activate_result = message.activate();
//     if (!activate_result)
//     {
//         CARB_LOG_ERROR("Activate pose tree %s", GxfResultStr(activate_result.error()));
//         return;
//     }

//     publish(mOutputComponent, mOutputChannel, std::move(message));
// }

// gxf_result_t PoseTreeComponent::addPrim(nvidia::gxf::Entity& message,
//                                         const pxr::UsdPrim& prim,
//                                         const int depth,
//                                         const nvidia::isaac::PoseTree::frame_t parentUid,
//                                         bool useLocalPose)
// {
//     const std::string path = prim.GetPath().GetString();

//     nvidia::isaac::PoseTree::frame_t poseUid;
//     if (mPrimRegexStr.empty() || std::regex_match(path, mPrimRegex))
//     {
//         auto maybeUid = mPoseTreeMap->findOrCreateNamedFrame(path);
//         if (!maybeUid)
//         {
//             CARB_LOG_ERROR("Create prim %s named pose frame fails", path.c_str());
//             return GXF_FAILURE;
//         }
//         // CARB_LOG_WARN("Create named pose for prim %s", path.c_str());
//         poseUid = maybeUid.value();
//     }
//     else
//     {
//         auto maybeUid = mPoseTreeMap->findOrCreateUnnamedFrame(path);
//         if (!maybeUid)
//         {
//             CARB_LOG_ERROR("Create prim %s unnamed pose frame fails", path.c_str());
//             return GXF_FAILURE;
//         }
//         // CARB_LOG_WARN("Create named pose for prim %s", path.c_str());
//         poseUid = maybeUid.value();
//     }

//     // Get pose of the prim
//     ::isaac::Pose3d pose = ::isaac::Pose3d::Identity();
//     omni::isaac::dynamic_control::DcObjectType prim_type =
//         mDynamicControlPtr->peekObjectType(prim.GetPath().GetString().c_str());
//     if (prim_type == omni::isaac::dynamic_control::eDcObjectArticulation)
//     {
//         DcHandle articulationHandle = mDynamicControlPtr->getArticulation(prim.GetPath().GetString().c_str());
//         DcHandle artRootBody = mDynamicControlPtr->getArticulationRootBody(articulationHandle);
//         // Calculate pose
//         DcTransform articulationPose = mDynamicControlPtr->getRigidBodyPose(artRootBody);
//         pxr::GfVec3d artTranslation = asGfVec3d(articulationPose.p);
//         pxr::GfQuatd artRotation = asGfQuatd(articulationPose.r);

//         // Converts to robot engine pose
//         toVector3d(artTranslation * mUnitScale, pose.translation);
//         toSO3d(artRotation, pose.rotation);
//         useLocalPose = false;
//     }
//     else if (prim_type == omni::isaac::dynamic_control::eDcObjectRigidBody)
//     {

//         DcHandle rigidBodyHandle = mDynamicControlPtr->getRigidBody(prim.GetPath().GetString().c_str());
//         // Calculate pose
//         DcTransform rigidBodyPose = mDynamicControlPtr->getRigidBodyPose(rigidBodyHandle);
//         pxr::GfVec3d rigidBodyTranslation = asGfVec3d(rigidBodyPose.p);
//         pxr::GfQuatd rigidBodyRotation = asGfQuatd(rigidBodyPose.r);
//         // Converts to robot engine pose
//         toVector3d(rigidBodyTranslation * mUnitScale, pose.translation);
//         toSO3d(rigidBodyRotation, pose.rotation);
//         useLocalPose = false;
//     }
//     else if (prim_type == omni::isaac::dynamic_control::eDcObjectNone)
//     {
//         // Calculate pose

//         pxr::UsdTimeCode primTimeCode = pxr::UsdTimeCode::Default();
//         std::vector<double> times;
//         pxr::UsdGeomXformable(prim).GetTimeSamples(&times);

//         if (times.size() > 1)
//         {
//             primTimeCode = round(mTimeline->getCurrentTime() * this->mStage->GetTimeCodesPerSecond());
//         }

//         pxr::GfQuatd usdBodyRotation;
//         pxr::GfVec3d usdBodyTranslation;
//         if (useLocalPose)
//         {
//             const pxr::GfTransform usdBodyPose(omni::usd::UsdUtils::getLocalTransformMatrix(prim, primTimeCode));
//             usdBodyTranslation = usdBodyPose.GetTranslation();
//             usdBodyRotation = usdBodyPose.GetRotation().GetQuat();
//         }
//         else
//         {
//             const pxr::GfTransform usdBodyPose(omni::usd::UsdUtils::getWorldTransformMatrix(prim, primTimeCode));
//             usdBodyTranslation = usdBodyPose.GetTranslation();
//             usdBodyRotation = usdBodyPose.GetRotation().GetQuat();
//         }
//         // Converts to robot engine proto message
//         toVector3d(usdBodyTranslation * mUnitScale, pose.translation);
//         toSO3d(usdBodyRotation, pose.rotation);
//     }


//     // Add PoseFrameUid component for lhs frame
//     const std::string lhs_component_name = "lhs_frame_" + std::to_string(mEdgeCount);
//     auto maybe_lhs_frame = message.add<nvidia::isaac::PoseFrameUid>(lhs_component_name.c_str());
//     if (!maybe_lhs_frame)
//     {
//         return maybe_lhs_frame.error();
//     }
//     maybe_lhs_frame.value()->uid = useLocalPose ? parentUid : mRootUid;

//     // Add PoseFrameUid component for rhs frame
//     const std::string rhs_component_name = "rhs_frame_" + std::to_string(mEdgeCount);
//     auto maybe_rhs_frame = message.add<nvidia::isaac::PoseFrameUid>(rhs_component_name.c_str());
//     if (!maybe_rhs_frame)
//     {
//         return maybe_rhs_frame.error();
//     }
//     maybe_rhs_frame.value()->uid = poseUid;

//     // Add PoseTreeSetEdge component
//     const std::string edge_component_name = "set_edge_info_" + std::to_string(mEdgeCount);
//     auto maybe_pose_tree_set_edge = message.add<nvidia::isaac::PoseTreeSetEdgeInfo>(edge_component_name.c_str());
//     if (!maybe_pose_tree_set_edge)
//     {
//         return maybe_pose_tree_set_edge.error();
//     }
//     const nvidia::gxf::Handle<nvidia::isaac::PoseTreeSetEdgeInfo> set_edge_info = maybe_pose_tree_set_edge.value();
//     set_edge_info->time = this->mTimeSeconds;
//     set_edge_info->lhs_T_rhs = pose;

//     mEdgeCount++;

//     // CARB_LOG_WARN("Set pose for prim %s", path.c_str());

//     if (depth == 0)
//     {
//         return GXF_SUCCESS;
//     }

//     // Add the current prim and its immediate descendants
//     pxr::UsdPrimSiblingRange range = prim.GetChildren();
//     for (pxr::UsdPrimSiblingRange::iterator iter = range.begin(); iter != range.end(); ++iter)
//     {
//         pxr::UsdPrim child_prim = *iter;
//         const auto result = addPrim(message, child_prim, depth - 1, poseUid, true);
//         if (result != GXF_SUCCESS)
//         {
//             return result;
//         }
//     }
//     return GXF_SUCCESS;
// }

// void PoseTreeComponent::onComponentChange()
// {
//     // CARB_LOG_ERROR("PoseTreeComponent Update");
//     GxfComponent::onComponentChange();

//     const pxr::RobotEngineBridgeSchemaRobotEnginePoseTree& typedPrim =
//         (pxr::RobotEngineBridgeSchemaRobotEnginePoseTree)mPrim;
//     isaac::utils::safeGetAttribute(typedPrim.GetOutputComponentAttr(), mOutputComponent);
//     isaac::utils::safeGetAttribute(typedPrim.GetOutputChannelAttr(), mOutputChannel);
//     isaac::utils::safeGetAttribute(typedPrim.GetDepthLimitsAttr(), mDepthLimits);
//     isaac::utils::safeGetAttribute(typedPrim.GetPrimRegexAttr(), mPrimRegexStr);

//     CARB_LOG_WARN("PoseTree regex string %s", mPrimRegexStr.c_str());

//     mPrimRegex = std::regex(mPrimRegex);

//     typedPrim.GetPrimsRel().GetTargets(&mPrims);

//     if (mPrims.size() != mDepthLimits.size())
//     {
//         CARB_LOG_ERROR("prims and depthLimits do not have same size");
//         return;
//     }
// }
// }
// }
// }
