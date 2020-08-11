#pragma once

#include <omni/isaac/urdf/UrdfTypes.h>

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
        std::vector<Node*> childNodes_;

        Node(std::string linkName, std::string parentJointName) : linkName_(linkName), parentJointName_(parentJointName)
        {
        }
    };

    Node* baseNode = nullptr;

    KinematicChain() = default;

    ~KinematicChain();

    // Computes the kinematic chain for a UrdfRobot description
    bool computeKinematicChain(const UrdfRobot& urdfRobot);

private:
    // Recursively finds a node's children
    void computeChildNodes(Node* parentNode, const UrdfRobot& urdfRobot);

    // Recursively deletes the tree
    void deleteNode(Node* node);
};

}
}
}
