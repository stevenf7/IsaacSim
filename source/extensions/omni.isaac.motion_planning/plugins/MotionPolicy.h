// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once


#include <carb/Framework.h>
#include <carb/filesystem/IFileSystem.h>
#include <carb/settings/ISettings.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/motion_planning/MotionPlanning.h>

// clang-format off
#include <omni/usd/UtilsIncludes.h>  // must be included before UsdUtils.h
#include <omni/usd/UsdUtils.h>
// clang-format on

// On Windows, Windows.h (insanely) defines a preprocessor macro called "ERROR",
// which conflicts with the ERROR log level in lula.h.  It also defines "PASSTHROUGH",
// which conflicts with an enum value in lula/math/df/sparse_affine_map.h.
#ifdef _MSC_VER
#    pragma push_macro("ERROR")
#    pragma push_macro("PASSTHROUGH")
#    undef ERROR
#    undef PASSTHROUGH
#endif // defined _MSC_VER

#include <lula/kinematics.h>
#include <lula/math/differential_geometry/state.h>
#include <lula/rmpflow/rmpflow_robot_policy.h>
#include <lula/world.h>

#ifdef _MSC_VER
#    pragma pop_macro("ERROR")
#    pragma pop_macro("PASSTHROUGH")
#endif // defined _MSC_VER

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
     * @param obstacle_path
     */
    void enableObstacle(const std::string& obstacle_path);
    /**
     * Disable obstacle
     * @param obstacle_path
     */
    void disableObstacle(const std::string& obstacle_path);
    /**
     * Indicate if obstacle exists in policy
     * @param obstacle_path
     *
     * @return true if obstacle_path represents a valid obstacle in policy
     * @return false if obstacle_path is not found
     */
    bool hasObstacle(const std::string& obstacle_path) const;

    /**
     * @brief Set the step frequency.
     *
     * @param newFrequency.
     */
    void setFrequency(const float newFrequency);

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


    std::shared_ptr<lula::World> mRmpflowWorld;
    lula::WorldView mRmpflowWorldView;
    std::shared_ptr<lula::rmp::RmpflowRobotPolicy> mRmpflowPolicy;
    bool mRmpflowPolicyInitialized{ false };
    std::shared_ptr<lula::Kinematics> mKinematics;
    lula::Kinematics::FrameHandle mEndEffectorFrame;

    // Obstacles
    std::unordered_map<std::string, std::pair<pxr::UsdPrim, lula::World::ObstacleHandle>> mRegisteredObstacles;

    // RMP State
    lula::math::State mState;
    Eigen::VectorXd q, qd;
    lula::Pose3 mEndEffectorPose;
    Eigen::Vector3d mTargetOrig, mTargetAxisX, mTargetAxisY, mTargetAxisZ;
    std::vector<double> mEndEffectorError;

    bool mOverrideDt;
    float mFixedDt;
    float mFrequency;
    double mUnitScale;
};
