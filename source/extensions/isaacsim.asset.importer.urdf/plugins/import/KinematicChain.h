// SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#pragma once

#include "../UrdfTypes.h"

#include <memory>
#include <string>
#include <vector>

namespace isaacsim
{
namespace asset
{
namespace importer
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
}
