// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
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

#include "isaacsim/core/utils/UsdUtilities.h"
#include "pxr/usd/usdPhysics/joint.h"
#include "sensor_msgs/JointState.h"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <isaacsim/core/utils/Math.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/physics/tensors/IArticulationView.h>
#include <omni/physics/tensors/ISimulationView.h>
#include <omni/physics/tensors/TensorApi.h>

#include <OgnROS1PublishJointStateDatabase.h>
#include <RosNode.h>

class OgnROS1PublishJointState : public RosNode
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS1PublishJointStateDatabase::sPerInstanceState<OgnROS1PublishJointState>(nodeObj, instanceId);

        state.m_tensorInterface = carb::getCachedInterface<omni::physics::tensors::TensorApi>();
        if (!state.m_tensorInterface)
        {
            CARB_LOG_ERROR("Failed to acquire Tensor Api interface\n");
            return;
        }
    }


    static bool compute(OgnROS1PublishJointStateDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.perInstanceState<OgnROS1PublishJointState>();
        const auto& prim = db.inputs.targetPrim();
        const char* primPath;
        if (prim.size() > 0)
        {
            primPath = omni::fabric::toSdfPath(prim[0]).GetText();
        }
        else
        {
            db.logError("Could not find target prim");
            return false;
        }

        // spin once calls reset automatically if it was not successful
        if (!state.spinOnce(db.inputs.nodeNamespace()))
        {

            return false;
        }

        // Publisher was not valid, create a new one
        if (!state.mPublisher)
        {
            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto m_stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
            state.m_simView = state.m_tensorInterface->createSimulationView(stageId);
            if (!m_stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }
            state.m_unitScale = UsdGeomGetStageMetersPerUnit(m_stage);


            // Verify we have a valid articulation prim
            state.m_articulation = state.m_simView->createArticulationView(std::vector<std::string>{ primPath });
            if (!state.m_articulation)
            {
                db.logError("Prim %s is not an articulation", primPath);
                return false;
            }

            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();

            if (!validateTopic(topicName))
            {
                return false;
            }
            state.mPublisher = std::make_unique<ros::Publisher>(
                state.mNodeHandle->advertise<sensor_msgs::JointState>(topicName, db.inputs.queueSize()));

            return true;
        }

        state.publishJointStates(db, context);
        return true;
    }

    template <typename T>
    static void createTensorDesc(omni::physics::tensors::TensorDesc& tensorDesc,
                                 std::vector<T>& buffer,
                                 int numElements,
                                 omni::physics::tensors::TensorDataType type)
    {
        buffer.resize(numElements);
        tensorDesc.dtype = type;
        tensorDesc.numDims = 1;
        tensorDesc.dims[0] = numElements;
        tensorDesc.data = buffer.data();
        tensorDesc.ownData = true;
        tensorDesc.device = -1;
    }

    void publishJointStates(OgnROS1PublishJointStateDatabase& db, const GraphContextObj& context)
    {
        double stageUnits = 1.0 / m_unitScale;
        sensor_msgs::JointState msg;
        msg.header.seq = 0;

        if (db.inputs.timeStamp() >= 0.0)
        {
            msg.header.stamp.fromSec(db.inputs.timeStamp());
        }
        else
        {
            db.logError("Timestamp is invalid");
            return;
        }
        long stageId = context.iContext->getStageId(context);
        m_stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
        uint32_t num_dofs = m_articulation->getMaxDofs();
        omni::physics::tensors::TensorDesc positionTensor;
        omni::physics::tensors::TensorDesc velocityTensor;
        omni::physics::tensors::TensorDesc effortTensor;
        omni::physics::tensors::TensorDesc dofTypeTensor;
        createTensorDesc(positionTensor, m_jointPositions, num_dofs, omni::physics::tensors::TensorDataType::eFloat32);
        createTensorDesc(velocityTensor, m_jointVelocities, num_dofs, omni::physics::tensors::TensorDataType::eFloat32);
        createTensorDesc(effortTensor, m_jointEfforts, num_dofs, omni::physics::tensors::TensorDataType::eFloat32);
        createTensorDesc(dofTypeTensor, m_dofTypes, num_dofs, omni::physics::tensors::TensorDataType::eUint8);
        bool hasDofStates = true;
        if (!m_articulation->getDofPositions(&positionTensor))
        {
            printf("Failed to get dof positions\n");
            hasDofStates = false;
        }
        if (!m_articulation->getDofVelocities(&velocityTensor))
        {
            printf("Failed to get dof velocities\n");
            hasDofStates = false;
        }
        if (!m_articulation->getDofProjectedJointForces(&effortTensor))
        {
            printf("Failed to get dof efforts\n");
            hasDofStates = false;
        }
        if (!m_articulation->getDofTypes(&dofTypeTensor))
        {
            printf("Failed to get dof types\n");
            hasDofStates = false;
        }

        if (hasDofStates)
        {
            for (uint32_t j = 0; j < num_dofs; j++)
            {
                const char* jointPath = m_articulation->getUsdDofPath(0, j);

                if (jointPath)
                {
                    msg.name.push_back(isaacsim::core::utils::GetName(m_stage->GetPrimAtPath(pxr::SdfPath(jointPath))));
                }

                if (omni::physics::tensors::DofType(m_dofTypes[j]) == omni::physics::tensors::DofType::eTranslation)
                {
                    msg.position.push_back(
                        isaacsim::core::utils::math::roundNearest(m_jointPositions[j] * stageUnits, 10000.0)); // m
                    msg.velocity.push_back(
                        isaacsim::core::utils::math::roundNearest(m_jointVelocities[j] * stageUnits, 10000.0)); // m/s
                    msg.effort.push_back(
                        isaacsim::core::utils::math::roundNearest(m_jointEfforts[j] * stageUnits, 10000.0)); // N
                }
                else
                {
                    msg.position.push_back(isaacsim::core::utils::math::roundNearest(m_jointPositions[j], 10000.0)); // rad
                    msg.velocity.push_back(isaacsim::core::utils::math::roundNearest(m_jointVelocities[j], 10000.0)); // rad/s
                    msg.effort.push_back(isaacsim::core::utils::math::roundNearest(
                        m_jointEfforts[j] * stageUnits * stageUnits, 10000.0)); // N*m
                }
            }
            mPublisher->publish(msg);
        }
    }


    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS1PublishJointStateDatabase::sPerInstanceState<OgnROS1PublishJointState>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        if (m_simView)
        {
            m_simView->release(true);
            m_simView = nullptr;
        }

        m_stage = nullptr;
        m_jointPositions.clear();
        m_jointVelocities.clear();
        m_jointEfforts.clear();
        m_dofTypes.clear();

        mPublisher.reset(); // This should be reset before we reset the handle.
        RosNode::reset();
    }

private:
    std::unique_ptr<ros::Publisher> mPublisher;

    pxr::UsdStageWeakPtr m_stage = nullptr;
    omni::physics::tensors::TensorApi* m_tensorInterface = nullptr;
    omni::physics::tensors::ISimulationView* m_simView = nullptr;
    omni::physics::tensors::IArticulationView* m_articulation = nullptr;
    std::vector<float> m_jointPositions;
    std::vector<float> m_jointVelocities;
    std::vector<float> m_jointEfforts;
    std::vector<uint8_t> m_dofTypes;

    double m_unitScale = 1;
};

REGISTER_OGN_NODE()
