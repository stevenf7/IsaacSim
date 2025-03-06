// Copyright (c) 2023-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <memory>
#include <string>
#include <vector>

namespace isaacsim
{
namespace ros2
{
namespace tf_viewer
{

/**
 * Class that partially implement a tf2 `BufferCore`.
 */
class Ros2BufferCore
{
public:
    /**
     * Add a transform information to the buffer.
     *
     * @param msg `TFMessage` message pointer.
     * @param authority The source of the information for the transform.
     * @param isStatic Wether to record the transform as static (the transform will be good across all time).
     * @returns Whether the transform has ben added.
     */
    virtual bool setTransform(void* msg, const std::string& authority, bool isStatic) = 0;

    /**
     * Get the transform between two frames at the ROS zero time.
     *
     * @param targetFrame Frame ID to which data should be transformed.
     * @param sourceFrame Frame ID where the data originated.
     * @param translation Buffer to store the Cartesian translation. Buffer length should be 3.
     * @param rotation Buffer to store the rotation (as quaternion: xyzw). Buffer length should be 4.
     * @returns Whether the transform has ben computed without exceptions.
     */
    virtual bool getTransform(const std::string& targetFrame,
                              const std::string& sourceFrame,
                              double translation[],
                              double rotation[]) = 0;

    /**
     * Get the parent frame of the specified frame at the ROS zero time.
     *
     * @param frame Frame ID to search for.
     * @param parentFrame Reference in which the parent frame ID will be stored.
     * @returns True, unless no parent exists.
     */
    virtual bool getParentFrame(const std::string& frame, std::string& parentFrame) = 0;

    /**
     * Get the available frame IDs.
     *
     * @returns A list of available frame IDs.
     */
    virtual std::vector<std::string> getFrames() = 0;

    /**
     * Clear all buffer data.
     */
    virtual void clear() = 0;
};


/**
 * Base class for creating ROS 2 tf2 related functions/objects according to the sourced ROS 2 distribution.
 */
class Tf2Factory
{
public:
    virtual ~Tf2Factory() = default;

    /**
     * Create a ROS 2 tf2 `BufferCore`.
     *
     * @returns Pointer to the buffer.
     */
    virtual std::shared_ptr<Ros2BufferCore> createBuffer() = 0;
};

} // namespace tf_viewer
} // namespace ros2
} // namespace isaacsim
