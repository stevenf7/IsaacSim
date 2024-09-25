// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#ifdef _WIN32
#    pragma warning(push)
#    pragma warning(disable : 4996)
#endif

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on
#include "omni/isaac/utils/UsdUtilities.h"

#include <include/Ros2Node.h>
#include <omni/isaac/utils/ScopedCudaDevice.h>

#include <OgnROS2PublishPointCloudDatabase.h>

using namespace isaacsim::ros2::bridge;

class OgnROS2PublishPointCloud : public Ros2Node
{
public:
    static bool compute(OgnROS2PublishPointCloudDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishPointCloud>();

        // Spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            db.logError("Unable to create ROS2 node, please check that namespace is valid");
            return false;
        }

        // Publisher was not valid, create a new one
        if (!state.m_publisher)
        {
            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(state.m_namespaceName, topicName);
            if (!state.m_factory->validateTopicName(fullTopicName))
            {
                db.logError("Unable to create ROS2 publisher, invalid topic name");
                return false;
            }

            state.m_message = state.m_factory->createPointCloudMessage();

            Ros2QoSProfile qos;
            const std::string& qosProfile = db.inputs.qosProfile();
            if (qosProfile == "")
            {
                qos.depth = db.inputs.queueSize();
            }
            else
            {
                if (!jsonToRos2QoSProfile(qos, qosProfile))
                {
                    return false;
                }
            }

            state.m_publisher = state.m_factory->createPublisher(
                state.m_nodeHandle.get(), fullTopicName.c_str(), state.m_message->getTypeSupportHandle(), qos);

            state.m_frameId = db.inputs.frameId();
            return true;
        }

        return state.publishLidar(db);
    }

    bool publishLidar(OgnROS2PublishPointCloudDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Lidar Point Cloud Pub");
        auto& state = db.perInstanceState<OgnROS2PublishPointCloud>();

        // Check if subscription count is 0
        if (!m_publishWithoutVerification && !state.m_publisher.get()->getSubscriptionCount())
        {
            return false;
        }

        size_t height = 1;
        uint32_t pointStep = sizeof(GfVec3f);
        size_t width = 0;
        size_t row_step = 0;

        if (db.inputs.cudaDeviceIndex() == -1)
        {
            if (db.inputs.dataPtr() != 0)
            {
                width = db.inputs.bufferSize() / pointStep;
                row_step = db.inputs.bufferSize();
                size_t totalBytes = row_step;
                state.m_message->generateBuffer(db.inputs.timeStamp(), m_frameId, width, height, pointStep);
                // Data is on host as ptr, buffer size matches
                memcpy(state.m_message->getBufferPtr(), reinterpret_cast<void*>(db.inputs.dataPtr()), totalBytes);
            }

            else if (db.inputs.dataPtr() == 0)
            {
                width = db.inputs.data.size();
                row_step = pointStep * db.inputs.data.size();
                size_t totalBytes = row_step;
                state.m_message->generateBuffer(db.inputs.timeStamp(), m_frameId, width, height, pointStep);
                // Data is on host as ogn data, copy from cpu
                memcpy(state.m_message->getBufferPtr(), reinterpret_cast<const uint8_t*>(db.inputs.data.cpu().data()),
                       totalBytes);
            }
        }
        else
        {
            if (db.inputs.dataPtr() != 0)
            {
                width = db.inputs.bufferSize() / pointStep;
                row_step = db.inputs.bufferSize();
                // size_t totalBytes = row_step;
                state.m_message->generateBuffer(db.inputs.timeStamp(), m_frameId, width, height, pointStep);

                omni::isaac::utils::ScopedDevice scopedDev(db.inputs.cudaDeviceIndex());
                auto src = reinterpret_cast<void*>(db.inputs.dataPtr());
                CUDA_CHECK(
                    cudaMemcpy(state.m_message->getBufferPtr(), src, db.inputs.bufferSize(), cudaMemcpyDeviceToHost));
            }
        }

        state.m_publisher.get()->publish(state.m_message->getPtr());
        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishPointCloudDatabase::sPerInstanceState<OgnROS2PublishPointCloud>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        m_publisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Publisher> m_publisher = nullptr;
    std::shared_ptr<Ros2PointCloudMessage> m_message = nullptr;

    std::string m_frameId = "sim_lidar";
};

REGISTER_OGN_NODE()

#ifdef _WIN32
#    pragma warning(pop)
#endif
