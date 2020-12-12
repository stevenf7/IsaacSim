// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once


#include "MotionPolicySuppressionToken.h"

#include <carb/Framework.h>
#include <carb/filesystem/IFileSystem.h>
#include <carb/settings/ISettings.h>

#include <Eigen/Geometry>
#include <lula/kinematics/robot.h>
#include <lula/kinematics/urdf_util.h>
#include <lula/math/differential_geometry/state.h>
#include <lula/math/geometry/distance_function3d_factory.h>
#include <lula/rmpflow/rmpflow_robot_policy.h>
#include <lula/rmpflow/rmpflow_robot_policy_factory.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/motion_planning/MotionPlanning.h>

// clang-format off
#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>
// clang-format on

/**
 * Defines a single RMP object and interfaces to configure, query and interact with that RMP
 */
class MotionPolicy
{
public:
    MotionPolicy(pxr::UsdStageWeakPtr stage, omni::isaac::dynamic_control::DynamicControl* dynamic_control);

    /**
     * Initialize the RMP with a specific control frame
     * @param robotUrdfPath the urdf description for the robot, contains additional control frames
     * @param robotDescriptorPath the robot specific RMP parameters
     * @param rmpFlowCommonPath the file containing RMP parametes
     * @param controlFrame control frame used for go_local commands
     */
    void initialize(const std::string& robotUrdfPath,
                    const std::string& robotDescriptorPath,
                    const std::string& rmpFlowCommonPath,
                    const std::string& controlFrame);
    /**
     * Resets the RMP to zero pose
     *
     */
    void reset();

    /**
     * Update the RMP and get the new state
     * @param t
     * @param dt
     */
    void step(const float t, const float dt);

    /**
     * Set the RMP target, specified in the global frame
     * @param position
     * @param rotation
     */
    void setTargetGlobal(const carb::Float3& position, const carb::Float4& rotation);

    /**
     * Set the RMP target, specified in the local frame of articulation prim
     * @param position
     * @param rotation
     */
    void setTargetLocal(const carb::Float3& position, const carb::Float4& rotation);

    /**
     * Specify end effector target in local reference frame
     * @param command List of partial pose target, one for the position of the control frame and one for each rotation
     * axis
     */
    void goLocal(const omni::isaac::motion_planning::PartialPoseCommand& command);

    /**
     * Get the current error in position
     * @return error
     */
    std::vector<double> getError();

    /**
     * Get current end effector state
     * @return origin, x axis, y axis, z axis state returned in that order.
     */
    std::vector<carb::Float3> getRmpState();
    /**
     * Get current end effector target
     * If RMP target is not specified for all axes the current state is returned
     * @return origin, x axis, y axis, z axis state returned in that order.
     */
    std::vector<carb::Float3> getRmpTarget();

    /**
     * Set default config for RMP
     * @param command
     */
    void setDefaultConfig(const std::vector<double>& config);

    /**
     * Add an obstacle to the RMP
     * @param obstacle_path
     * @param type
     * @param scale
     */
    void addObstacle(const std::string& obstacle_path, const int type, const carb::Float3 scale);

    /**
     * Update obstacle pose
     * @param obstacle_path
     */
    void updateObstacle(const std::string& obstacle_path);

    /**
     * Update obstacle pose
     * @param obstacle_path
     * @param T
     */
    void updateObstacle(const std::string& obstacle_path, const omni::isaac::dynamic_control::DcTransform& T);

    /**
     * Remove obstacle
     * @param obstacle_path
     */
    void removeObstacle(const std::string& obstacle_path);
    /**
     * Enable obstacle
     * @param command
     */
    void enableObstacle(const std::string& obstacle_path);
    /**
     * Disable obstacle
     * @param command
     */
    void disableObstacle(const std::string& obstacle_path);

    /**
     * @brief Set the step frequency.
     *
     * @param newFrequency.
     * @param useFixedDt.
     */
    void setFrequency(const float newFrequency, bool useFixedDt);

    /**
     * @brief Set the Prim corresponding to the articulation controlled by this RMP
     *
     * @param prim
     * @return true if prim was an articulation with a root
     * @return false if prim is not an articulation or root was not found
     */
    bool setRobotPrim(const pxr::UsdPrim& prim);

    /**
     * @brief Get the DC handle for the root of the articulation used by this RMP
     *
     * @return omni::isaac::dynamic_control::DcHandle
     */
    omni::isaac::dynamic_control::DcHandle getRobotRootHandle();

private:
    // Global pointers:
    pxr::UsdStageWeakPtr mStage = nullptr;
    omni::isaac::dynamic_control::DynamicControl* mDynamicControl = nullptr;


    pxr::UsdPrim mRobotPrim;
    omni::isaac::dynamic_control::DcHandle mRobotHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    omni::isaac::dynamic_control::DcHandle mRobotRootHandle = omni::isaac::dynamic_control::kDcInvalidHandle;


    std::shared_ptr<lula::rmp::RmpflowRobotPolicy> mRmpflowPolicy;

    // Task maps that are evaluated with current RMP state to get end effector state
    std::shared_ptr<const lula::rmp::TaskMap> mOrigMap;
    std::shared_ptr<const lula::rmp::TaskMap> mAxisXMap;
    std::shared_ptr<const lula::rmp::TaskMap> mAxisYMap;
    std::shared_ptr<const lula::rmp::TaskMap> mAxisZMap;

    // Obstacles
    std::unordered_map<std::string, std::pair<pxr::UsdPrim, std::shared_ptr<lula::math::PosableDistanceFunction3d>>>
        mRegisteredObstacleDistanceFunctions;
    std::shared_ptr<lula::math::DistanceFunction3dFactory> mDistanceFunction3DFactory;
    std::shared_ptr<MotionPolicySuppressionToken> mRegisteredSuppressionTokens;

    // RMP State
    lula::math::State mState;
    Eigen::VectorXd q, qd;
    Eigen::Vector3d mOrigFk, mAxisXFk, mAxisYFk, mAxisZFk;
    Eigen::Vector3d mTargetOrig, mTargetAxisX, mTargetAxisY, mTargetAxisZ;
    std::vector<double> mEndEffectorError;
    std::vector<carb::Float3> mEndEffectorState;
    std::vector<carb::Float3> mEndEffectorTarget;

    bool mOverrideDt;
    float mFixedDt;
    int mFrequency;
    double mUnitScale;
};
