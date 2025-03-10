// Copyright (c) 2023-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include "Conversions.h"
#include "Pose.h"
#include "UsdUtilities.h"

#include <foundation/PxTransform.h>
#include <isaacSensorSchema/isaacRtxLidarSensorAPI.h>
#include <omni/usd/UsdUtils.h>
#include <physx/include/foundation/PxTransform.h>
#include <usdrt/scenegraph/usd/rt/xformable.h>

#include <DynamicControl.h>

using namespace isaacsim::core::includes::conversions;

namespace isaacsim
{
namespace core
{
namespace includes
{
namespace posetree
{

/**
 * @class PoseTree
 * @brief A utility class for managing and traversing hierarchical pose transformations in a scene.
 * @details
 * PoseTree provides functionality to manage and process pose transformations between different frames
 * in a hierarchical scene structure. It handles both rigid bodies and articulated objects, computing
 * relative transforms between parent and child frames.
 *
 * The class supports:
 * - Parent-child relationships between prims
 * - Rigid body transformations
 * - Articulation hierarchies
 * - Camera-specific transformations
 *
 * @note This class requires a valid USD stage and DynamicControl instance to function properly.
 * @warning Frame names must be unique within the tree. Duplicate names will be automatically renamed
 *          with their full path.
 */
class PoseTree
{
public:
    /**
     * @brief Constructs a new PoseTree instance.
     * @details Initializes the PoseTree with USD stage and dynamic control references.
     *
     * @param[in] stageId The unique identifier for the USD stage
     * @param[in] dynamicControlPtr Pointer to the DynamicControl instance for physics interactions
     *
     * @pre stageId must be valid and correspond to an existing USD stage
     * @pre dynamicControlPtr must be a valid pointer to a DynamicControl instance
     */
    PoseTree(const uint64_t& stageId, omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    {
        // Store the USD and USDRT stage references from the stage ID
        m_usdStage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(static_cast<long>(stageId)));
        omni::fabric::IStageReaderWriter* iStageReaderWriter =
            carb::getCachedInterface<omni::fabric::IStageReaderWriter>();
        omni::fabric::StageReaderWriterId stageInProgress = iStageReaderWriter->get(stageId);
        m_usdrtStage = usdrt::UsdStage::Attach(stageId, stageInProgress);

        m_dynamicControlPtr = dynamicControlPtr;
    }

    /**
     * @brief Sets the parent prim path and frame name for the pose tree.
     * @details Establishes the root reference frame for subsequent pose calculations.
     *
     * @param[in] parentPath SDF path for the parent prim in the USD stage
     * @param[in] parentFrame Name identifier for the parent frame
     *
     * @note The parent frame serves as the root reference for all child transformations
     */
    void setParentPrimPath(const pxr::SdfPath& parentPath, const std::string& parentFrame)
    {
        m_parentPath = parentPath;
        m_parentFrame = parentFrame;
    }

    /**
     * @brief Sets the target prim paths to be processed in the pose tree.
     * @details Defines the set of prims whose poses will be computed relative to the parent frame.
     *
     * @param[in] targets Vector of SDF paths representing the target prims
     */
    void setTargetPrimPaths(const pxr::SdfPathVector& targets)
    {
        m_targets = targets;
    }

    /**
     * @brief Traverses the complete pose tree and processes each transform.
     * @details
     * Performs a depth-first traversal of the pose tree, computing transforms between parent and child frames.
     * Handles different types of prims including:
     * - Articulations and their bodies
     * - Rigid bodies
     * - Regular transforms
     * - Special cases like cameras
     *
     * @param[in] processTransform Callback function to handle each computed transform
     *
     * @note The callback function receives:
     *       - Parent frame name (string)
     *       - Child frame name (string)
     *       - Relative transform between frames (PxTransform)
     *
     * @warning For cameras without RTXLidar API, an additional 180-degree rotation about the x-axis is applied
     */
    void processAllFrames(
        std::function<void(const std::string&, const std::string&, const ::physx::PxTransform&)>& processTransform)
    {
        // If the parent prim path is not empty, get the type of prim and its pose.
        if (!m_parentPath.IsEmpty())
        {
            omni::isaac::dynamic_control::DcObjectType type =
                m_dynamicControlPtr->peekObjectType(m_parentPath.GetString().c_str());
            if (type == omni::isaac::dynamic_control::eDcObjectRigidBody)
            {
                m_parentPose = getRigidBodyPose(m_parentPath);
            }
            else if (type == omni::isaac::dynamic_control::eDcObjectNone ||
                     type == omni::isaac::dynamic_control::eDcObjectArticulation)
            {
                m_parentPose = getXformPose(m_parentPath);
            }

            m_parentFrame =
                getUniqueFrameName(getName(m_usdStage->GetPrimAtPath(m_parentPath)), m_parentPath.GetString());
        }
        // For each target prim determine its type and compute the associated poses
        for (pxr::SdfPath primPath : m_targets)
        {
            omni::isaac::dynamic_control::DcObjectType type =
                m_dynamicControlPtr->peekObjectType(primPath.GetString().c_str());
            if (type == omni::isaac::dynamic_control::eDcObjectArticulation)
            {
                omni::isaac::dynamic_control::DcHandle artculationHandle =
                    m_dynamicControlPtr->getArticulation(primPath.GetString().c_str());
                omni::isaac::dynamic_control::DcHandle rootBody =
                    m_dynamicControlPtr->getArticulationRootBody(artculationHandle);
                ::physx::PxTransform body1Pose = asPxTransform(m_dynamicControlPtr->getRigidBodyPose(rootBody));

                std::string framePath(m_dynamicControlPtr->getRigidBodyPath(rootBody));
                std::string bodyName = getName(m_usdStage->GetPrimAtPath(pxr::SdfPath(framePath)));

                if (!m_parentPath.IsEmpty())
                {
                    body1Pose = m_parentPose.transformInv(body1Pose);
                }
                std::string childFrameId = getUniqueFrameName(bodyName, framePath);
                if (m_parentFrame != childFrameId)
                {
                    // articulations always have an extra transform to the base link/rigid body
                    processTransform(m_parentFrame, childFrameId, body1Pose);
                }
                size_t numDofs = m_dynamicControlPtr->getArticulationBodyCount(artculationHandle);
                for (size_t j = 0; j < numDofs; j++)
                {
                    omni::isaac::dynamic_control::DcHandle parentBody =
                        m_dynamicControlPtr->getArticulationBody(artculationHandle, j);
                    ::physx::PxTransform body0Pose = asPxTransform(m_dynamicControlPtr->getRigidBodyPose(parentBody));
                    std::string parentPath(m_dynamicControlPtr->getRigidBodyPath(parentBody));
                    std::string parentName = getName(m_usdStage->GetPrimAtPath(pxr::SdfPath(parentPath)));
                    size_t numJoints = m_dynamicControlPtr->getRigidBodyChildJointCount(parentBody);
                    for (size_t k = 0; k < numJoints; k++)
                    {
                        omni::isaac::dynamic_control::DcHandle joint =
                            m_dynamicControlPtr->getRigidBodyChildJoint(parentBody, k);
                        omni::isaac::dynamic_control::DcHandle child_body = m_dynamicControlPtr->getJointChildBody(joint);


                        ::physx::PxTransform body1Pose = asPxTransform(m_dynamicControlPtr->getRigidBodyPose(child_body));
                        ::physx::PxTransform body0Tbody1(body0Pose.transformInv(body1Pose));
                        std::string framePath(m_dynamicControlPtr->getRigidBodyPath(child_body));
                        auto bodyName = getName(m_usdStage->GetPrimAtPath(pxr::SdfPath(framePath)));

                        processTransform(getUniqueFrameName(parentName, parentPath),
                                         getUniqueFrameName(bodyName, framePath), body0Tbody1);
                    }
                }
            }
            else if (type == omni::isaac::dynamic_control::eDcObjectRigidBody)
            {
                ::physx::PxTransform body1Pose = getRigidBodyPose(primPath);

                std::string childFrameId =
                    getUniqueFrameName(getName(m_usdStage->GetPrimAtPath(primPath)), primPath.GetString());
                if (m_parentFrame != childFrameId)
                {
                    if (!m_parentPath.IsEmpty())
                    {
                        body1Pose = m_parentPose.transformInv(body1Pose);
                    }


                    processTransform(m_parentFrame, childFrameId, body1Pose);
                }
            }
            else if (type == omni::isaac::dynamic_control::eDcObjectNone)
            {
                pxr::UsdPrim prim = m_usdStage->GetPrimAtPath(primPath);

                ::physx::PxTransform body1Pose = getXformPose(primPath);


                if (prim.IsA<pxr::UsdGeomCamera>() && !prim.HasAPI<pxr::IsaacSensorIsaacRtxLidarSensorAPI>())
                {
                    // Regular camera (not RTXLidar), Rotate 180 degrees about x-axis
                    // pxr::GfMatrix4d(1, 0, 0, 0, 0, -1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1);
                    ::physx::PxQuat omniTCamera(1, 0, 0, 0);
                    body1Pose = body1Pose * ::physx::PxTransform(omniTCamera);
                }

                if (!m_parentPath.IsEmpty())
                {
                    body1Pose = m_parentPose.transformInv(body1Pose);
                }

                processTransform(m_parentFrame, getUniqueFrameName(getName(prim), primPath.GetString()), body1Pose);
            }
        }
    }

    /**
     * @brief Retrieves the physics-based pose of a rigid body.
     * @details Queries the DynamicControl system for the current pose of a rigid body prim.
     *
     * @param[in] path SDF path to the rigid body prim
     * @return PxTransform representing the world-space pose of the rigid body
     *
     * @pre The prim at the specified path must be a valid rigid body
     */
    ::physx::PxTransform getRigidBodyPose(const pxr::SdfPath& path)
    {
        omni::isaac::dynamic_control::DcHandle rigidBodyHandle =
            m_dynamicControlPtr->getRigidBody(path.GetString().c_str());
        return asPxTransform(m_dynamicControlPtr->getRigidBodyPose(rigidBodyHandle));
    }

    /**
     * @brief Gets the pose of a prim using fabric or USD.
     * @details Computes the world-space transform of a prim, prioritizing fabric data if available.
     *
     * @param[in] path SDF path to the target prim
     * @return PxTransform representing the world-space pose of the prim
     */
    ::physx::PxTransform getXformPose(const pxr::SdfPath& path)
    {
        return asPxTransform(isaacsim::core::includes::pose::computeWorldXformNoCache(m_usdStage, m_usdrtStage, path));
    }

    /**
     * @brief Generates a unique frame name for a given prim.
     * @details
     * Ensures unique frame names by:
     * 1. Using the provided frame name if unique
     * 2. Using a cached renamed version if previously processed
     * 3. Creating a new unique name based on the full path if needed
     *
     * @param[in] frame Desired frame name
     * @param[in] path Full USD path of the prim
     * @return std::string Unique frame name
     *
     * @note If a name collision occurs, the full path is used with '/' replaced by '_'
     * @warning Logs a warning when name collisions occur, suggesting the use of isaac:nameOverride
     */
    std::string getUniqueFrameName(const std::string& frame, const std::string& path)
    {
        std::string name(frame);
        if (m_renamedFrames.find(path) != m_renamedFrames.end())
        {
            m_publishedFrames[frame] = true;
            return m_renamedFrames[path];
        }
        else if (m_publishedFrames.find(frame) == m_publishedFrames.end())
        {
            m_renamedFrames[path] = frame;
            m_publishedFrames[frame] = true;
        }

        else
        {
            name = path;
            std::replace(name.begin(), name.end(), '/', '_');
            name = name.substr(1);
            CARB_LOG_WARN(
                "Frame with name %s already exists. Overriding frame name for %s to %s (you can add the attribute isaac:nameOverride to remove this warning)",
                frame.c_str(), path.c_str(), name.c_str());
            m_renamedFrames[path] = name;
            m_publishedFrames[name] = true;
        }
        return name;
    }

    /**
     * @brief Retrieves the world pose of a frame.
     * @details Computes the world-space transform of a frame, prioritizing fabric data if available.
     *
     * @param[in] frame Frame name
     * @param[in] getParent If true, retrieves the pose of the parent frame
     * @return PxTransform representing the world-space pose of the frame
     */
    ::physx::PxTransform getFrameWorldPose(const std::string& frame, bool getParent = false)
    {
        pxr::SdfPath path(frame);
        if (getParent)
        {
            path = path.GetParentPath();
        }
        return asPxTransform(isaacsim::core::includes::pose::computeWorldXformNoCache(m_usdStage, m_usdrtStage, path));
    }

private:
    /** @brief SDF path to the parent prim */
    pxr::SdfPath m_parentPath;

    /** @brief Name identifier for the parent frame */
    std::string m_parentFrame;

    /** @brief Vector of target prim paths to process */
    pxr::SdfPathVector m_targets;

    /** @brief Cached transform of the parent frame */
    ::physx::PxTransform m_parentPose = ::physx::PxTransform(::physx::PxIdentity);

    /** @brief Reference to the USD stage */
    pxr::UsdStageRefPtr m_usdStage;

    /** @brief Reference to the USDRT stage */
    usdrt::UsdStageRefPtr m_usdrtStage;

    /** @brief Pointer to the DynamicControl instance */
    omni::isaac::dynamic_control::DynamicControl* m_dynamicControlPtr = nullptr;

    /** @brief Map of original paths to renamed frames */
    std::map<std::string, std::string> m_renamedFrames;

    /** @brief Set of published frame names */
    std::map<std::string, bool> m_publishedFrames;
};
}
}
}
}
