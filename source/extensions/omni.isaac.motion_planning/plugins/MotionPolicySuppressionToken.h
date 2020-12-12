// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <lula/rmpflow/obstacle_suppression_token.h>

#include <string>
#include <unordered_map>

/**
 * Defines interface used to suppress and unsuppress obstacles
 */
class MotionPolicySuppressionToken : public lula::rmp::ObstacleSuppressionToken
{
public:
    MotionPolicySuppressionToken();
    /**
     * Adds an obstacle to this suppression token with a defined state.
     * Existing entries are overwritten with the provided state value
     * Both current and target activation are set to the state value
     */
    void Add(const std::string& obstacleName, const double state = 1.0);

    /**
     * Removes an obstacle from this supression token.
     *
     * @param obstacleName string specifying name of obstacle to remove.
     * @return false if the given obstacleName does not exist
     */
    bool Remove(const std::string& obstacleName);

    /**
     * Disable an obstacle from this suppression token
     * Sets its target activation to 0.0
     *
     * @param obstacleName string specifying name of obstacle to disable.
     * @return false if the given obstacleName does not exist
     */
    bool Disable(const std::string& obstacleName);

    /**
     * Enable an obstacle from this suppression token
     * Sets its target activation to 1.0
     *
     * @param obstacleName string specifying name of obstacle to enable.
     * @return false if the given obstacleName does not exist
     */
    bool Enable(const std::string& obstacleName);

    /**
     * Steps current activations for all obstacles on this token until they equals the target activation.
     * current activation is always clamped between 0.0 and 1.0.
     * @param step speed at which current activation increases or decreases to match the target.
     */
    void Update(const double step = 0.02);
    /**
     * Get the current activation for an obstacle
     * @param obstacleName string specifying name of obstacle to get activation for.
     * @return value between 0.0 and 1.0
     */
    double Activation(const std::string& obstacleName) const;

private:
    std::unordered_map<std::string, double> mActivations;
    std::unordered_map<std::string, double> mTargetActivations;
};
