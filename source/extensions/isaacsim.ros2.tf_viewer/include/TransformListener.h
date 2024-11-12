// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once
#include <carb/Interface.h>

namespace isaacsim
{
namespace ros2
{
namespace tf_viewer
{

/**
 * ROS 2 transform listener interface
 */
class ITransformListener
{
public:
    CARB_PLUGIN_INTERFACE("isaacsim::ros2::tf_viewer::ITransformListener", 1, 0);

    /**
     * Initialize the transform listener by loading the adequate ROS 2 plugin and creating the tf2 buffer.
     *
     * @returns Wether the transform listener was initialized successfully.
     */
    virtual bool initialize(const std::string& rosDistro) = 0;

    /**
     * Finalize subscriptions to the tf (if any) and reset ROS 2 node.
     */
    virtual void finalize() = 0;

    /**
     * Do transform listener to record incoming tf transforms.
     *
     * @returns True if there is the tf messages has been taken without error, false otherwise.
     */
    virtual bool spin() = 0;

    /**
     * Reset the internal buffer by clearing its data.
     */
    virtual void reset() = 0;

    /**
     * Compute all transforms with respect to the specified (root) frame.
     *
     * @param rootFrame Frame ID on which to compute transforms.
     */
    virtual void computeTransforms(const std::string& rootFrame) = 0;

    /**
     * Get the available frame IDs.
     *
     * It is necessary to call the \ref computeTransforms method first before invoking this one to obtain updated data.
     *
     * @returns A list of available frame IDs.
     */
    virtual const std::vector<std::string>& getFrames() = 0;

    /**
     * Get the relations between available frame IDs.
     *
     * It is necessary to call the \ref computeTransforms method first before invoking this one to obtain updated data.
     *
     * @returns A list of relation-pairs between frame IDs.
     */
    virtual const std::vector<std::tuple<std::string, std::string>>& getRelations() = 0;

    /**
     * Get the transforms of the available frame IDs with respect to the specified (root) frame.
     *
     * It is necessary to call the \ref computeTransforms method first before invoking this one to obtain updated data.
     *
     * @returns A map of transforms (translation: xyz, rotation: xyzw) of each frame IDs.
     */
    virtual const std::unordered_map<std::string,
                                     std::tuple<std::tuple<double, double, double>, std::tuple<double, double, double, double>>>&
    getTransforms() = 0;
};

} // namespace tf_viewer
} // namespace ros2
} // namespace isaacsim
