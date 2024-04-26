// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <include/Ros2Node.h>
#include <omni/fabric/FabricUSD.h>
#include <physxSchema/physxArticulationAPI.h>
#include <pxr/usd/usdPhysics/articulationRootAPI.h>
#include <pxr/usd/usdPhysics/collisionAPI.h>
#include <pxr/usd/usdPhysics/fixedJoint.h>
#include <pxr/usd/usdPhysics/meshCollisionAPI.h>
#include <pxr/usd/usdPhysics/rigidBodyAPI.h>

#include <OgnROS2SubscribeTransformTreeDatabase.h>


class OgnROS2SubscribeTransformTree : public Ros2Node
{

public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS2SubscribeTransformTreeDatabase::sPerInstanceState<OgnROS2SubscribeTransformTree>(nodeObj, instanceId);

        state.mUsdStage = nullptr;
        state.mAnonLayer = nullptr;
        state.nodeId = nodeObj.nodeHandle;

        state.startupState = 0;
    }

    static bool compute(OgnROS2SubscribeTransformTreeDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2SubscribeTransformTree>();

        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            db.logError("Unable to create ROS2 node, please check that namespace is valid");
            return false;
        }

        // Subscriber was not valid, create a new one
        if (!state.mSubscriber)
        {
            //  Find our stage
            state.mUsdStage = omni::usd::UsdContext::getContext()->getStage();
            if (!state.mUsdStage)
            {
                db.logError("Could not find USD stage");
                return false;
            }

            // Create subscriber
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(state.mNamespaceName, topicName);
            if (!state.mFactory->validateTopic(fullTopicName))
            {
                db.logError("Unable to create ROS2 subscriber, invalid topic name");
                return false;
            }


            // Create message and subscriber
            state.mMessage = state.mFactory->CreateTfTreeMessage();

            Ros2QoSProfile qos;

            const std::string& qosProfile = db.inputs.qosProfile();
            if (qosProfile == "")
            {
                qos.depth = db.inputs.queueSize();
            }
            else
            {
                if (!jsonToRos2QoSProfile(qos, qosProfile))
                {
                    return false;
                }
            }
            state.mSubscriber = state.mFactory->CreateSubscriber(
                state.mNodeHandle.get(), fullTopicName.c_str(), state.mMessage->getTypeSupportHandle(), qos);


            return true;
        }

        return state.subscriberCallback(db);
    }


    static void releaseInstance(const NodeObj& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS2SubscribeTransformTreeDatabase::sPerInstanceState<OgnROS2SubscribeTransformTree>(nodeObj, instanceId);
        state.reset();
    }

    /**
     * @brief Reset the node
     * Note that we need to reset the subscriber first so it doesn't get called again, then the callback, and then call
     * the base class reset
     *
     */
    virtual void reset()
    {
        startupState = 0;

        if (mAnonLayer == nullptr)
            return;

        mSubscriber.reset(); // This should be reset before we reset the handle.

        Ros2Node::reset();

        // IMPORTANT NOTE
        // It seems that removing the anonymous layer triggers some sort of internal update in
        // OmniGraph that destroys and recreates all the nodes.  This causes releaseInstance to
        // be called, followed by deconstruction of this node.  When returnning from the Remove
        // method this instance of the node will have already been deconstructed, so any changes
        // after the removal can result in memory corruption.  A cleaner approach would be
        // queueing up some sort of function that gets called later, which handles removing
        // the layer.
        auto anonLayer = mAnonLayer;
        auto usdStage = mUsdStage;
        mAnonLayer.Reset();
        mAnonLayer = nullptr;
        mUsdStage = nullptr;

        pxr::SdfLayerHandle session = usdStage->GetSessionLayer();
        session->GetSubLayerPaths().Remove(anonLayer->GetIdentifier());
    }


    bool subscriberCallback(OgnROS2SubscribeTransformTreeDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2SubscribeTransformTree>();

        // An error occured when we parsed the inputs
        if (startupState == -1)
        {
            return false;
        }

        // First tick, we set things up and disable physics
        if (startupState == 0)
        {
            // Get the mapping from ROS2 frame to prim, and other stuff
            if (!buildFramePrimsMapAndSet(db))
            {
                startupState = -1;
                return false;
            }

            disablePhysicsArticulationAPIs(db);

            startupState++;

            return true;
        }

        if (startupState == 1)
        {
            disablePhysicsRigidBodiesAndJoints(db);

            startupState++;

            return true;
        }

        bool gotMessage = false;

        // Receive all the messages that are available
        while (state.mSubscriber->spin(state.mMessage->ptr()))
        {
            pxr::UsdEditContext editContext(mUsdStage, mAnonLayer);

            gotMessage = true;

            // Get the tfMessages
            std::vector<tfMessageStruct> tfMsg_vec;
            state.mMessage->getData(tfMsg_vec);

            for (size_t i = 0; i < tfMsg_vec.size(); i++)
            {
                std::string childFrame = tfMsg_vec[i].childFrame;
                std::string parentFrame = tfMsg_vec[i].parentFrame;

                if (mFramePrimsMap.count(childFrame) == 0)
                    continue;

                if (mFramePrimsMap.count(parentFrame) == 0)
                {
                    // db.logWarning("Could not find parent frame %s", parentFrame.c_str());
                    continue;
                }


                // We are given TFMessages with a transform between the child and parent frame, however in the scene
                // the corresponding prim may have a different parent.  Given a child to parent transform,
                // we need to calculate the child to usd parent transform.  This is done by combining child to parent,
                // parent to world and the inverse of the usd parent to world transforms

                std::string childPrimPath = mFramePrimsMap[childFrame];
                std::string parentPrimPath = mFramePrimsMap[parentFrame];

                pxr::UsdPrim childPrim = mUsdStage->GetPrimAtPath(pxr::SdfPath(childPrimPath));
                pxr::UsdPrim parentPrim = mUsdStage->GetPrimAtPath(pxr::SdfPath(parentPrimPath));
                pxr::UsdPrim usdParentPrim = childPrim.GetParent();

                pxr::GfMatrix4d parentToWorldTransform = omni::usd::UsdUtils::getWorldTransformMatrix(parentPrim);
                pxr::GfMatrix4d usdParentToWorldTransform = omni::usd::UsdUtils::getWorldTransformMatrix(usdParentPrim);

                // The transform we're given in the TFMessage
                pxr::GfMatrix4d childTransform;

                childTransform.SetIdentity();
                childTransform.SetTranslateOnly(
                    pxr::GfVec3d(tfMsg_vec[i].trans_x, tfMsg_vec[i].trans_y, tfMsg_vec[i].trans_z));
                childTransform.SetRotateOnly(pxr::GfQuatd(
                    tfMsg_vec[i].quat_w, pxr::GfVec3d(tfMsg_vec[i].quat_x, tfMsg_vec[i].quat_y, tfMsg_vec[i].quat_z)));


                // Now compose the final child to usd parent transform
                pxr::GfMatrix4d newChildTransform;
                newChildTransform = childTransform * parentToWorldTransform * usdParentToWorldTransform.GetInverse();


                // Extract the translation and rotation from our new transform
                pxr::GfVec3d translation, scale;
                pxr::GfQuatd rotation;
                translation = newChildTransform.ExtractTranslation();
                rotation = newChildTransform.ExtractRotationQuat();
                scale.Set(1.0, 1.0, 1.0);


                // Next we take our new translation rotation and scale, and apply it to our prim.
                // Since this may be in a reference, we are unable to clear out all the new xformOps.
                // Below we go through the existing xformOps, either creating or overwriting the existing
                // ones.  Then we set the xformOp order.
                pxr::UsdGeomXform xform(childPrim);

                pxr::UsdGeomXformOp translateXformOp, orientXformOp, scaleXformOp;


                // Go through existing xformOps, extracting the translate, orient and scale ones
                bool resetsXFormStack = false;
                std::vector<pxr::UsdGeomXformOp> xformOps = xform.GetOrderedXformOps(&resetsXFormStack);

                for (const pxr::UsdGeomXformOp& xformOp : xformOps)
                {
                    if (xformOp.GetOpType() == pxr::UsdGeomXformOp::TypeTranslate)
                        translateXformOp = xformOp;
                    else if (xformOp.GetOpType() == pxr::UsdGeomXformOp::TypeOrient)
                        orientXformOp = xformOp;
                    else if (xformOp.GetOpType() == pxr::UsdGeomXformOp::TypeScale)
                        scaleXformOp = xformOp;
                }

                // Add the XformOps if they didn't exist
                if (!translateXformOp)
                    translateXformOp =
                        xform.AddXformOp(pxr::UsdGeomXformOp::TypeTranslate, pxr::UsdGeomXformOp::PrecisionDouble);

                if (!orientXformOp)
                    orientXformOp =
                        xform.AddXformOp(pxr::UsdGeomXformOp::TypeOrient, pxr::UsdGeomXformOp::PrecisionDouble);

                if (!scaleXformOp)
                    scaleXformOp = xform.AddXformOp(pxr::UsdGeomXformOp::TypeScale, pxr::UsdGeomXformOp::PrecisionDouble);

                // Set the XformOps with the proper precision
                if (translateXformOp.GetPrecision() == pxr::UsdGeomXformOp::PrecisionDouble)
                    translateXformOp.Set(translation);
                else
                    translateXformOp.Set(pxr::GfVec3f(translation));

                if (orientXformOp.GetPrecision() == pxr::UsdGeomXformOp::PrecisionDouble)
                    orientXformOp.Set(rotation);
                else
                    orientXformOp.Set(pxr::GfQuatf(rotation));

                if (scaleXformOp.GetPrecision() == pxr::UsdGeomXformOp::PrecisionDouble)
                    scaleXformOp.Set(scale);
                else
                    scaleXformOp.Set(pxr::GfVec3f(scale));

                // Clear the old xformOpOrder, and set the new one
                xform.ClearXformOpOrder();
                xform.SetXformOpOrder({ translateXformOp, orientXformOp, scaleXformOp });
            }
        }

        if (gotMessage)
            db.outputs.execOut() = kExecutionAttributeStateEnabled;

        return gotMessage;
    }

    void disablePhysicsArticulationAPIs(OgnROS2SubscribeTransformTreeDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2SubscribeTransformTree>();

        std::string layerName = "anon_ros2_subscribe_transform_tree_" + std::to_string(state.nodeId);

        // Create anonymous layer, where we disable the physics on the articulation / prims,
        // and where we update the transforms
        state.mAnonLayer = pxr::SdfLayer::CreateAnonymous(layerName);
        pxr::SdfLayerHandle session = state.mUsdStage->GetSessionLayer();

        session->GetSubLayerPaths().push_back(state.mAnonLayer->GetIdentifier());

        pxr::UsdEditContext editContext(state.mUsdStage, state.mAnonLayer);
        {
            pxr::SdfChangeBlock changeBlock;

            // Disable the articulation API on all the provide articulation roots
            for (const std::string& path : state.mArticulationRoots)
            {
                pxr::UsdPrim prim = state.mUsdStage->GetPrimAtPath(pxr::SdfPath(path));

                if (!prim.HasAPI<pxr::PhysxSchemaPhysxArticulationAPI>())
                {
                    db.logWarning("Articulation Root %s doesn't have PhysxSchemaPhysxArticulationAPI", path.c_str());
                    continue;
                }

                pxr::PhysxSchemaPhysxArticulationAPI articulationAPI(prim);
                articulationAPI.GetArticulationEnabledAttr().Set(false);
            }
        }
    }


    void disablePhysicsRigidBodiesAndJoints(OgnROS2SubscribeTransformTreeDatabase& db)
    {
        pxr::UsdEditContext editContext(mUsdStage, mAnonLayer);
        {
            pxr::SdfChangeBlock changeBlock;

            // Disable rigid bodies, and joints that connect pairs of prims in our articulation
            for (const pxr::UsdPrim& prim : mUsdStage->Traverse())
            {
                if (prim.IsA<pxr::UsdPhysicsJoint>())
                {
                    pxr::UsdPhysicsJoint joint(prim);

                    pxr::SdfPathVector targets0, targets1;
                    joint.GetBody0Rel().GetTargets(&targets0);
                    joint.GetBody1Rel().GetTargets(&targets1);
                    if (targets0.size() == 0 || targets1.size() == 0)
                        continue;

                    if (mPrimPaths.count(targets0.at(0).GetPrimPath().GetString()) > 0 ||
                        mPrimPaths.count(targets1.at(0).GetPrimPath().GetString()) > 0)
                    {
                        joint.GetJointEnabledAttr().Set(false);
                    }
                }

                if (mPrimPaths.count(prim.GetPath().GetString()) > 0)
                {
                    if (!prim.HasAPI<pxr::UsdPhysicsRigidBodyAPI>())
                        continue;

                    pxr::UsdPhysicsRigidBodyAPI rigidBody(prim);

                    rigidBody.GetRigidBodyEnabledAttr().Set(false);
                }
            }
        }
    }


private:
    bool buildFramePrimsMapAndSet(OgnROS2SubscribeTransformTreeDatabase& db)
    {

        auto& state = db.perInstanceState<OgnROS2SubscribeTransformTree>();

        state.mFramePrimsMap.clear();
        state.mPrimPaths.clear();
        state.mArticulationRoots.clear();

        if (db.inputs.frameNamesMap().size() % 2 != 0)
        {
            db.logError("The frameNamesMap must have an even length in OgnROS2SubscribeTransformTree node");
            return false;
        }

        // Read in the frameNamesMap, checking for duplicates
        for (std::size_t i = 0; i < db.inputs.frameNamesMap().size() / 2; ++i)
        {
            const std::string isaacPrimPath = db.tokenToString(db.inputs.frameNamesMap()[2 * i]);
            const std::string frameName = db.tokenToString(db.inputs.frameNamesMap()[2 * i + 1]);

            if (state.mPrimPaths.count(isaacPrimPath) != 0)
            {
                db.logError("Encountered duplicate prim path \"%s\" in OgnROS2SubscribeTransformTree frameNamesMap",
                            isaacPrimPath.c_str());
                return false;
            }
            if (state.mFramePrimsMap.count(frameName) != 0)
            {
                db.logError("Encountered duplicate frame name \"%s\" in OgnROS2SubscribeTransformTree frameNamesMap",
                            frameName.c_str());
                return false;
            }

            if (!state.mUsdStage->GetPrimAtPath(pxr::SdfPath(isaacPrimPath)))
            {
                db.logError("The provided prim path \"%s\" is invalid in OgnROS2SubscribeTransformTree frameNamesMap",
                            isaacPrimPath.c_str());
                return false;
            }

            state.mFramePrimsMap[frameName] = isaacPrimPath;
            state.mPrimPaths.insert(isaacPrimPath);
        }

        for (std::size_t i = 0; i < db.inputs.articulationRoots().size(); ++i)
        {

            const std::string articulationPath = db.tokenToString(db.inputs.articulationRoots()[i]);

            pxr::UsdPrim prim = state.mUsdStage->GetPrimAtPath(pxr::SdfPath(articulationPath));

            if (!prim || !prim.HasAPI<pxr::PhysxSchemaPhysxArticulationAPI>())
            {
                db.logError(
                    "Articulation Root \"%s\" doesn't have PhysxSchemaPhysxArticulationAPI in OgnROS2SubscribeTransformTree node",
                    articulationPath.c_str());
                return false;
            }
            state.mArticulationRoots.push_back(articulationPath);
        }

        return true;
    }


    std::shared_ptr<Ros2Subscriber> mSubscriber = nullptr;
    std::shared_ptr<Ros2TfTreeMessage> mMessage = nullptr;

    std::map<std::string, std::string> mFramePrimsMap;
    std::set<std::string> mPrimPaths;
    std::vector<std::string> mArticulationRoots;

    long mStageId;
    pxr::UsdStageRefPtr mUsdStage;
    pxr::SdfLayerRefPtr mAnonLayer;

    uint64_t nodeId;
    int startupState = 0;
};

REGISTER_OGN_NODE()
