// SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <isaacsim/ucx/nodes/UcxPublishJointStateNodeBase.h>

#include <OgnUCXPublishJointStateDatabase.h>

using namespace isaacsim::ucx::nodes;

/**
 * @class OgnUCXPublishJointState
 * @brief OmniGraph node for publishing joint states via UCX.
 * @details
 * This node publishes robot joint state data over UCX using tagged communication.
 * It reads joint data from upstream input ports (e.g. connected from Isaac Read Joint State).
 */
class OgnUCXPublishJointState : public UCXPublishJointStateNodeBase<OgnUCXPublishJointStateDatabase>
{
public:
    /**
     * @brief Release the node instance.
     * @details
     * Cleans up resources when the node instance is destroyed.
     *
     * @param[in] nodeObj The node object
     * @param[in] instanceId The instance ID
     */
    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnUCXPublishJointStateDatabase::sPerInstanceState<OgnUCXPublishJointState>(nodeObj, instanceId);
        state.reset();
    }

    /**
     * @brief Compute function - called when node is executed.
     * @details
     * Extracts inputs, gets the per-instance state, and delegates to the base class logic.
     * Triggers the execution output port upon successful execution.
     *
     * @param[in] db Database accessor for node inputs/outputs
     * @return bool True if execution succeeded, false otherwise
     */
    static bool compute(OgnUCXPublishJointStateDatabase& db)
    {
        auto& state = db.template perInstanceState<OgnUCXPublishJointState>();

        const uint16_t port = static_cast<uint16_t>(db.inputs.port());
        const uint64_t tag = db.inputs.tag();
        const uint32_t timeoutMs = db.inputs.timeoutMs();

        bool success = state.computeImpl(db, port, tag, timeoutMs);

        if (success)
        {
            db.outputs.execOut() = kExecutionAttributeStateEnabled;
        }

        return success;
    }

protected:
    /**
     * @brief Extract joint state data from input ports.
     *
     * @param[in] db Database accessor for node inputs
     * @return JointStateData Extracted joint state data
     */
    isaacsim::ucx::nodes::JointStateData extractData(OgnUCXPublishJointStateDatabase& db) override
    {
        isaacsim::ucx::nodes::JointStateData data;
        data.timestamp = db.inputs.timeStamp();
        auto positions = db.inputs.jointPositions();
        auto velocities = db.inputs.jointVelocities();
        auto efforts = db.inputs.jointEfforts();
        data.numJoints = static_cast<uint32_t>(positions.size());
        data.positions.assign(positions.begin(), positions.end());
        data.velocities.assign(velocities.begin(), velocities.end());
        data.efforts.assign(efforts.begin(), efforts.end());
        return data;
    }

    /**
     * @brief Generate message from joint state data.
     * @details
     * Serializes joint state data into message format.
     * Message format:
     * - timestamp (double, 8 bytes)
     * - num_joints (uint32_t, 4 bytes)
     * - For each joint:
     *   - position (double, 8 bytes)
     *   - velocity (double, 8 bytes)
     *   - effort (double, 8 bytes)
     *
     * @param[in] data Joint state data to serialize
     * @return std::vector<uint8_t> Serialized message data
     */
    std::vector<uint8_t> generateMessage(const isaacsim::ucx::nodes::JointStateData& data) override
    {
        if (data.numJoints == 0)
        {
            return {};
        }

        // Calculate message size (using doubles for better precision)
        const size_t messageSize = sizeof(double) + sizeof(uint32_t) + data.numJoints * (sizeof(double) * 3);

        std::vector<uint8_t> messageData(messageSize);
        size_t offset = 0;

        // Write timestamp
        std::memcpy(messageData.data() + offset, &data.timestamp, sizeof(double));
        offset += sizeof(double);

        // Write number of joints
        std::memcpy(messageData.data() + offset, &data.numJoints, sizeof(uint32_t));
        offset += sizeof(uint32_t);

        // Write joint data (interleaved position, velocity, effort)
        for (uint32_t i = 0; i < data.numJoints; ++i)
        {
            std::memcpy(messageData.data() + offset, &data.positions[i], sizeof(double));
            offset += sizeof(double);

            std::memcpy(messageData.data() + offset, &data.velocities[i], sizeof(double));
            offset += sizeof(double);

            std::memcpy(messageData.data() + offset, &data.efforts[i], sizeof(double));
            offset += sizeof(double);
        }

        return messageData;
    }
};

REGISTER_OGN_NODE()
