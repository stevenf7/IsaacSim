// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include <Utils/IsaacConversions.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/utils/Conversions.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>
#include <plugins/Core/GxfNode.h>

#include <OgnGXFPublishPoseTreeDatabase.h>
#include <regex>
using namespace omni::isaac::gxf_bridge;
using namespace omni::isaac::dynamic_control;
using omni::isaac::utils::conversions::asGfMatrix4d;
using omni::isaac::utils::conversions::asGfQuatd;
using omni::isaac::utils::conversions::asGfVec3d;

class OgnGXFPublishPoseTree : public GxfNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnGXFPublishPoseTreeDatabase::sInternalState<OgnGXFPublishPoseTree>(nodeObj);
        state.mDynamicControlPtr = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();
        state.mThisPrimPath = nodeObj.iNode->getPrimPath(nodeObj);
        if (!state.mDynamicControlPtr)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
            return;
        }
    }

    static bool compute(OgnGXFPublishPoseTreeDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();
        auto& state = db.internalState<OgnGXFPublishPoseTree>();
        if (!state.getGxfContext())
        {
            if (state.setGxfContext(db.inputs.context()) != GXF_SUCCESS)
            {
                CARB_LOG_ERROR("Cannot set context");
                return false;
            }
        }
        //  Find our stage
        long stageId = context.iContext->getStageId(context);
        auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

        if (!stage)
        {
            db.logError("Could not find USD stage %ld", stageId);
            return false;
        }
        // Retrieve stage unit scale
        state.mUnitScale = UsdGeomGetStageMetersPerUnit(stage);
        // Retrieve pose tree.
        nvidia::isaac::PoseTree& poseTree = state.mAtlas->pose_tree();
        // Create or get the root simulation frame.
        const std::string& rootFrameName = db.inputs.rootFrame();
        auto maybeUid = poseTree.findOrCreateFrame(rootFrameName.c_str());
        if (!maybeUid)
        {
            CARB_LOG_ERROR("Unable to create or find root pose frame %s", rootFrameName.c_str());
            return false;
        }
        state.mRootUid = maybeUid.value();
        //  Finding target prims
        const auto& targetPrims = db.inputs.targetPrims();

        if (targetPrims.size() > 0)
        {
            state.mPrims.resize(targetPrims.size());
            std::transform(targetPrims.begin(), targetPrims.end(), state.mPrims.begin(),
                           [](TargetPath path) { return omni::fabric::toSdfPath(path); });
        }
        else
        {
            db.logError("Please specify atleast one target prim for the ROS pose tree component");
            return false;
        }

        state.buildFrameNameMap(db);

        std::size_t numPrims = state.mPrims.size();
        std::size_t numRegex = db.inputs.primRegex().size();
        if (numRegex > 0 && numRegex != numPrims)
        {
            CARB_LOG_ERROR_ONCE(
                "Regex list must be of the same size as target root prims, but input regex "
                "list has size %lu and target prims has size %lu",
                numRegex, numPrims);
            return false;
        }
        std::size_t numDepth = db.inputs.poseDepth().size();
        if (numDepth > 0 && numDepth != numPrims)
        {
            CARB_LOG_ERROR_ONCE(
                "Depth list must be of the same size as target root prims, but input depth "
                "list has size %lu and target prims has size %lu",
                numDepth, numPrims);
            return false;
        }

        // Loop over each prim
        for (size_t i = 0; i < state.mPrims.size(); i++)
        {
            pxr::UsdPrim prim = stage->GetPrimAtPath(state.mPrims[i]);
            const std::string primRegexStr =
                db.inputs.primRegex().size() > 0 ? db.tokenToString(db.inputs.primRegex()[i]) : "";
            if (!prim)
            {
                CARB_LOG_WARN("prim %s does not exist", state.mPrims[i].GetString().c_str());
                continue;
            }
            auto primDepths = db.inputs.poseDepth();
            int depth = 0;
            if (primDepths.size() > 0)
            {
                depth = primDepths.data()[i];
            }
            const pxr::GfMatrix4d identity = pxr::GfMatrix4d();
            // Initial root prim starts from nothing, no prefix.
            state.addPrimToPoseTree(prim, depth, primRegexStr, identity, "", state.mRootUid, false, false, db);
        }
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

private:
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    double mUnitScale = 1.0;
    nvidia::isaac::PoseTree::frame_t mRootUid;
    pxr::SdfPathVector mPrims;
    const char* mThisPrimPath = nullptr;
    std::map<std::string, std::string> mFrameNameMap;

    void buildFrameNameMap(const OgnGXFPublishPoseTreeDatabase& db)
    {
        for (std::size_t i = 0; i < db.inputs.frameNamesMap().size() / 2; ++i)
        {
            const std::string isaacPrimName = db.tokenToString(db.inputs.frameNamesMap()[2 * i]);
            const std::string atlasFrameName = db.tokenToString(db.inputs.frameNamesMap()[2 * i + 1]);
            mFrameNameMap[isaacPrimName] = atlasFrameName;
        }
    }

    void addPrimToPoseTree(const pxr::UsdPrim& prim,
                           const int depth,
                           const std::string& primRegexStr,
                           const pxr::GfMatrix4d& actualParentToWorld,
                           const std::string& parentName,
                           const nvidia::isaac::PoseTree::frame_t parentUid,
                           bool useLocalPose,
                           bool parentWasSkipped,
                           OgnGXFPublishPoseTreeDatabase& db)
    {
        auto& state = db.internalState<OgnGXFPublishPoseTree>();
        // Get both full prim path for regex matching and prim name for frame name
        const std::string fullPrimPath = prim.GetPath().GetString();
        const std::string primName = prim.GetName().GetString();
        // Build frame name by appending previous parent frames with a / separator.
        auto iterator = mFrameNameMap.find(fullPrimPath);
        std::string frameName = parentName.empty() ? primName : parentName + "/" + primName;
        if (iterator != mFrameNameMap.end())
        {
            frameName = iterator->second;
        }
        nvidia::isaac::PoseTree::frame_t poseUid{ 0 };
        nvidia::isaac::PoseTree& poseTree = state.mAtlas->pose_tree();
        // const std::string primRegexStr = db.inputs.primRegex();
        const std::regex primRegex = std::regex(primRegexStr);
        // std::shared_ptr<GxfPoseTreeMap> poseTreeMap = state.getPoseTreeMap();
        // First, check if this prim needs to be published in the pose tree.
        bool keepPrim = primRegexStr.empty() || std::regex_match(fullPrimPath, primRegex);
        if (keepPrim)
        {
            // If yes, create or find it.
            auto maybeUid = poseTree.findOrCreateFrame(frameName.c_str());
            if (!maybeUid)
            {
                CARB_LOG_ERROR("Unable to create prim %s named pose frame", frameName.c_str());
                return;
            }
            poseUid = maybeUid.value();
        }
        else
        {
            // If not, no need to create it in the pose tree.
            if (depth == 0)
            {
                // If we are a leaf, no need to get anything further at this point.
                return;
            }
        }
        // Get pose of the prim
        ::nvidia::isaac::Pose3d pose = ::nvidia::isaac::Pose3d::Identity();
        omni::isaac::dynamic_control::DcObjectType prim_type =
            mDynamicControlPtr->peekObjectType(prim.GetPath().GetString().c_str());
        pxr::GfMatrix4d currentPrimToWorld;
        pxr::GfMatrix4d currentPrimToParent;
        pxr::GfVec3d currentTranslation;
        pxr::GfQuatd currentQuat;
        // Current prim position has to be retrieved specifically if the prim is an articulation
        // or a rigid body.
        if (prim_type == omni::isaac::dynamic_control::eDcObjectArticulation)
        {
            DcHandle articulationHandle = mDynamicControlPtr->getArticulation(prim.GetPath().GetString().c_str());
            DcHandle artRootBody = mDynamicControlPtr->getArticulationRootBody(articulationHandle);
            // Calculate pose
            DcTransform articulationPose = mDynamicControlPtr->getRigidBodyPose(artRootBody);
            currentPrimToWorld = asGfMatrix4d(articulationPose);
            currentTranslation = asGfVec3d(articulationPose.p);
            currentQuat = asGfQuatd(articulationPose.r);
            useLocalPose = false;
        }
        else if (prim_type == omni::isaac::dynamic_control::eDcObjectRigidBody)
        {

            DcHandle rigidBodyHandle = mDynamicControlPtr->getRigidBody(prim.GetPath().GetString().c_str());
            // Calculate pose
            DcTransform rigidBodyPose = mDynamicControlPtr->getRigidBodyPose(rigidBodyHandle);
            currentPrimToWorld = asGfMatrix4d(rigidBodyPose);
            currentTranslation = asGfVec3d(rigidBodyPose.p);
            currentQuat = asGfQuatd(rigidBodyPose.r);
            useLocalPose = false;
        }
        else if (prim_type == omni::isaac::dynamic_control::eDcObjectNone)
        {
            // Calculate pose
            pxr::UsdTimeCode primTimeCode = pxr::UsdTimeCode::Default();

            currentPrimToWorld = omni::usd::UsdUtils::getWorldTransformMatrix(prim, primTimeCode);
            // If useLocalPose, we are attaching a prim to its parent.
            if (useLocalPose)
            {
                // Check if the parent prim is actually in the pose tree. If it is not,
                // we need to get the pose of the actual parent.
                if (parentWasSkipped)
                {
                    // The actual parent to world transform has been passed recursively.
                    currentPrimToParent = currentPrimToWorld * actualParentToWorld.GetInverse();
                }
                // Else we use the built in api.
                else
                {
                    currentPrimToParent = omni::usd::UsdUtils::getLocalTransformMatrix(prim, primTimeCode);
                }
                const pxr::GfTransform usdBodyPose(currentPrimToParent);
                currentTranslation = usdBodyPose.GetTranslation();
                currentQuat = usdBodyPose.GetRotation().GetQuat();
            }
            // Else we just get the pose relative to the root prim (sim).
            else
            {
                const pxr::GfTransform usdBodyPose(currentPrimToWorld);
                currentTranslation = usdBodyPose.GetTranslation();
                currentQuat = usdBodyPose.GetRotation().GetQuat();
            }
        }
        // If the prim should be in the pose tree, set its pose.
        if (keepPrim)
        {
            // Converts to robot engine pose
            toVector3d(currentTranslation * mUnitScale, pose.translation);
            toSO3d(currentQuat, pose.rotation);
            const std::string name_in_tree = poseTree.getFrameName(poseUid).value();
            if (useLocalPose)
            {
                // db.logWarning("Setting pose %f %f %f %f %f %f between %s (%ld) and %s (%ld) at time %f",
                //     pose.translation.x(), pose.translation.y(), pose.translation.z(),
                //     pose.rotation.eulerAnglesRPY()[0], pose.rotation.eulerAnglesRPY()[1],
                //     pose.rotation.eulerAnglesRPY()[2], parentName.c_str(), parentUid, frameName.c_str(), poseUid,
                //     mClock->time());
                // Here we set the pose relative to the parent frame. The parent id has
                // been recursively passed to be an id that exists and is in the tree.
                const auto result = poseTree.set(parentUid, poseUid, mClock->time(), pose);
                if (!result)
                {
                    db.logWarning(
                        "Unable to set pose for %s_T_%s: %d", parentName.c_str(), frameName.c_str(), result.error());
                    return;
                }
            }
            else
            {
                const std::string rootName = db.inputs.rootFrame();
                // db.logWarning("Setting pose %f %f %f %f %f %f between %s (%ld) and %s (%ld) at time %f",
                //     pose.translation.x(), pose.translation.y(), pose.translation.z(),
                //     pose.rotation.eulerAnglesRPY()[0], pose.rotation.eulerAnglesRPY()[1],
                //     pose.rotation.eulerAnglesRPY()[2], rootName.c_str(), mRootUid, frameName.c_str(), poseUid,
                //     mClock->time());
                // Set pose tree relative to simulation root frame
                const auto result = poseTree.set(mRootUid, poseUid, mClock->time(), pose);
                if (!result)
                {
                    db.logWarning("Unable to set pose for sim_T_%s: %d", frameName.c_str(), result.error());
                    return;
                }
            }
        }
        if (depth == 0)
        {
            return;
        }

        // Recursively call the method on the prim descendant
        pxr::UsdPrimSiblingRange range = prim.GetChildren();
        for (pxr::UsdPrimSiblingRange::iterator iter = range.begin(); iter != range.end(); ++iter)
        {
            pxr::UsdPrim child_prim = *iter;
            // Take care of having the correct parent position, frame id and name
            // if we skip the intermediary prims we need to keep track.
            const pxr::GfMatrix4d parentToWorld = keepPrim ? currentPrimToWorld : actualParentToWorld;
            const nvidia::isaac::PoseTree::frame_t actualParentUid = !keepPrim ? parentUid : poseUid;
            const std::string actualParentName = keepPrim ? frameName : parentName;
            addPrimToPoseTree(child_prim, depth - 1, primRegexStr, parentToWorld, actualParentName, actualParentUid,
                              true, !keepPrim, db);
        }
    }
};

REGISTER_OGN_NODE()
