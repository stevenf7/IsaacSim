// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <omni/isaac/urdf/UrdfTypes.h>

#include <memory>
#include <string>
#include <vector>

namespace omni
{
namespace isaac
{
namespace urdf
{

// Represents the kinematic chain as a tree
class KinematicChain
{
public:
    // A tree representing a link with its parent joint and child links
    struct Node
    {
        std::string linkName_;
        std::string parentJointName_;
        std::vector<std::unique_ptr<Node>> childNodes_;

        Node(std::string linkName, std::string parentJointName) : linkName_(linkName), parentJointName_(parentJointName)
        {
        }
    };

    std::unique_ptr<Node> baseNode;

    KinematicChain() = default;

    ~KinematicChain();

    // Computes the kinematic chain for a UrdfRobot description
    bool computeKinematicChain(const UrdfRobot& urdfRobot);

private:
    // Recursively finds a node's children
    void computeChildNodes(std::unique_ptr<Node>& parentNode, const UrdfRobot& urdfRobot);
};

}
}
}
