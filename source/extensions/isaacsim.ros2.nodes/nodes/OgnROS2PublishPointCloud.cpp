// SPDX-FileCopyrightText: Copyright (c) 2021-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

#ifdef _WIN32
#    pragma warning(push)
#    pragma warning(disable : 4996)
#endif

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <carb/profiler/Profile.h>
#include <carb/tasking/ITasking.h>
#include <carb/tasking/TaskingUtils.h>

#include <isaacsim/ros2/core/Ros2Node.h>
#include <isaacsim/ros2/nodes/PointCloudPublisher.h>

#include <GenericModelOutput.h>
#include <OgnROS2PublishPointCloudDatabase.h>

using namespace isaacsim::ros2::core;

class OgnROS2PublishPointCloud : public Ros2Node
{
public:
    static bool compute(OgnROS2PublishPointCloudDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishPointCloud>();
        const auto& nodeObj = db.abi_node();

        if (!state.m_pub.isInitialized())
        {
            const GraphContextObj& context = db.abi_context();
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            if (!state.m_pub.initialize(
                    std::string(nodeObj.iNode->getPrimPath(nodeObj)),
                    collectNamespace(db.inputs.nodeNamespace(),
                                     stage->GetPrimAtPath(pxr::SdfPath(nodeObj.iNode->getPrimPath(nodeObj)))),
                    db.inputs.topicName(), db.inputs.frameId(), db.inputs.queueSize(), db.inputs.qosProfile(),
                    db.inputs.context()))
            {
                db.logError("Unable to create ROS2 publisher");
                return false;
            }

            carb::settings::ISettings* threadSettings = carb::getCachedInterface<carb::settings::ISettings>();
            static constexpr char s_kThreadDisable[] = "/exts/isaacsim.ros2.bridge/publish_multithreading_disabled";
            state.m_multithreadingDisabled = threadSettings->getAsBool(s_kThreadDisable);
            return true;
        }

        return state.publishLidar(db);
    }


    bool publishFromGMO(OgnROS2PublishPointCloudDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "[IsaacSim] Publish PointCloud from GMO");
        auto& state = db.perInstanceState<OgnROS2PublishPointCloud>();
        auto tasking = carb::getCachedInterface<carb::tasking::ITasking>();

        auto* gmo = omni::sensors::getModelOutputPtrFromBuffer(reinterpret_cast<void*>(db.inputs.gmoDataPtr()));
        if (!gmo || gmo->numElements == 0)
        {
            CARB_LOG_INFO("ROS2PublishPointCloud: GMO buffer is empty or invalid. Skipping.");
            return false;
        }

        const size_t numElements = static_cast<size_t>(gmo->numElements);
        const auto modality = gmo->modality;
        const auto auxType = gmo->auxType;

        if (m_pcBuffer.capacity() == 0)
        {
            const size_t reserveSize = static_cast<size_t>(db.inputs.gmoMaxElements());
            m_pcBuffer.reserve(reserveSize);
            m_timestampBuffer.reserve(reserveSize);
        }
        m_pcBuffer.resize(numElements);
        m_timestampBuffer.resize(numElements);

        // Build Cartesian point cloud from GMO elements
        {
            CARB_PROFILE_ZONE(1, "[IsaacSim] GMO Point Cloud Conversion");
            const float* xData = gmo->elements.x;
            const float* yData = gmo->elements.y;
            const float* zData = gmo->elements.z;
            float3* pcOut = m_pcBuffer.data();

            if (gmo->elementsCoordsType == omni::sensors::CoordsType::CARTESIAN)
            {
                // Data is already Cartesian — direct copy
                tasking->parallelFor(size_t(0), numElements,
                                     [=](size_t idx) { pcOut[idx] = make_float3(xData[idx], yData[idx], zData[idx]); });
            }
            else
            {
                // Spherical to Cartesian conversion
                const float degToRad = static_cast<float>(M_PI) / 180.0f;
                constexpr float kMinDistance = 1e-6f;

                tasking->parallelFor(size_t(0), numElements,
                                     [=](size_t idx)
                                     {
                                         const float r = zData[idx];
                                         if (r < kMinDistance)
                                         {
                                             pcOut[idx] = make_float3(0.f, 0.f, 0.f);
                                         }
                                         else
                                         {
                                             const float az = xData[idx] * degToRad;
                                             const float el = yData[idx] * degToRad;
                                             const float rxy = r * cosf(el);
                                             pcOut[idx] = make_float3(rxy * cosf(az), rxy * sinf(az), r * sinf(el));
                                         }
                                     });
            }
        }

        // Extract metadata pointers from GMO based on selectedMetadata tokens
        float* intensityPtr = nullptr;
        uint64_t* timestampPtr = nullptr;
        uint32_t* emitterIdPtr = nullptr;
        uint32_t* channelIdPtr = nullptr;
        uint32_t* materialIdPtr = nullptr;
        uint32_t* tickIdPtr = nullptr;
        GfVec3f* hitNormalPtr = nullptr;
        GfVec3f* velocityPtr = nullptr;
        uint32_t* objectIdPtr = nullptr;
        uint8_t* echoIdPtr = nullptr;
        uint8_t* tickStatePtr = nullptr;
        float* radialVelocityMSPtr = nullptr;

        omni::sensors::LidarAuxiliaryData* lidarAux = nullptr;
        omni::sensors::RadarAuxiliaryData* radarAux = nullptr;
        if (auxType > omni::sensors::AuxType::NONE)
        {
            if (modality == omni::sensors::Modality::LIDAR)
                lidarAux = reinterpret_cast<omni::sensors::LidarAuxiliaryData*>(gmo->auxiliaryData);
            else if (modality == omni::sensors::Modality::RADAR)
                radarAux = reinterpret_cast<omni::sensors::RadarAuxiliaryData*>(gmo->auxiliaryData);
        }

        // Extract metadata pointers based on boolean inputs
        if (db.inputs.outputIntensity())
        {
            intensityPtr = const_cast<float*>(gmo->elements.scalar);
        }
        if (db.inputs.outputTimestamp())
        {
            if (numElements > m_timestampBuffer.size())
                m_timestampBuffer.resize(numElements);
            const uint64_t baseNs = gmo->timestampNs;
            const int32_t* offsets = gmo->elements.timeOffsetNs;
            uint64_t* tsDst = m_timestampBuffer.data();
            tasking->parallelFor(
                size_t(0), numElements, [=](size_t idx) { tsDst[idx] = baseNs + static_cast<uint64_t>(offsets[idx]); });
            timestampPtr = m_timestampBuffer.data();
        }
        if (db.inputs.outputEmitterId() && lidarAux)
        {
            emitterIdPtr = lidarAux->emitterId;
        }
        if (db.inputs.outputChannelId() && lidarAux)
        {
            channelIdPtr = lidarAux->channelId;
        }
        if (db.inputs.outputMaterialId() && lidarAux)
        {
            materialIdPtr = lidarAux->matId;
        }
        if (db.inputs.outputTickId() && lidarAux)
        {
            tickIdPtr = lidarAux->tickId;
        }
        if (db.inputs.outputHitNormal() && lidarAux)
        {
            hitNormalPtr = reinterpret_cast<GfVec3f*>(lidarAux->hitNormals);
        }
        if (db.inputs.outputVelocity() && lidarAux)
        {
            velocityPtr = reinterpret_cast<GfVec3f*>(lidarAux->velocities);
        }
        if (db.inputs.outputObjectId() && lidarAux)
        {
            objectIdPtr = reinterpret_cast<uint32_t*>(lidarAux->objId);
        }
        if (db.inputs.outputEchoId() && lidarAux)
        {
            echoIdPtr = lidarAux->echoId;
        }
        if (db.inputs.outputTickState() && lidarAux)
        {
            tickStatePtr = lidarAux->tickStates;
        }
        if (db.inputs.outputRadialVelocityMS() && radarAux)
        {
            radialVelocityMSPtr = radarAux->rv_ms;
        }

        // Generate and publish message (host path — GMO data is always on host)
        const size_t bufferSize = numElements * sizeof(float3);
        state.m_pub.getPointCloudMessage()->setUsePinnedBuffer(false);
        state.m_pub.getPointCloudMessage()->generateBuffer(db.inputs.timeStamp(), state.m_pub.getFrameId(), bufferSize,
                                                           intensityPtr, timestampPtr, emitterIdPtr, channelIdPtr,
                                                           materialIdPtr, tickIdPtr, hitNormalPtr, velocityPtr,
                                                           objectIdPtr, echoIdPtr, tickStatePtr, radialVelocityMSPtr);

        if (state.m_pub.getPointCloudMessage()->getOrderedFields().empty())
        {
            memcpy(state.m_pub.getPointCloudMessage()->getBufferPtr(), m_pcBuffer.data(),
                   state.m_pub.getPointCloudMessage()->getTotalBytes());
        }
        else
        {
            isaacsim::ros2::nodes::fillPointCloudBufferHost(
                reinterpret_cast<uint8_t*>(state.m_pub.getPointCloudMessage()->getBufferPtr()), m_pcBuffer.data(),
                state.m_pub.getPointCloudMessage()->getOrderedFields(),
                state.m_pub.getPointCloudMessage()->getPointStep(), state.m_pub.getPointCloudMessage()->getNumPoints());
        }

        if (state.m_multithreadingDisabled)
        {
            CARB_PROFILE_ZONE(1, "[IsaacSim] Publish PCL from GMO");
            state.m_pub.send();
        }
        else
        {
            tasking->addTask(carb::tasking::Priority::eHigh, state.m_tasks,
                             [&state]
                             {
                                 CARB_PROFILE_ZONE(1, "[IsaacSim] Publish PCL from GMO Thread");
                                 state.m_pub.send();
                             });
        }

        return true;
    }

    bool publishLidar(OgnROS2PublishPointCloudDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "[IsaacSim] Lidar Point Cloud Pub");
        auto& state = db.perInstanceState<OgnROS2PublishPointCloud>();
        auto tasking = carb::getCachedInterface<carb::tasking::ITasking>();

        {
            CARB_PROFILE_ZONE(1, "[IsaacSim] wait for previous publish");
            state.m_tasks.wait();
        }

        // GMO path: process GenericModelOutput buffer directly
        if (db.inputs.gmoDataPtr() != 0)
        {
            return publishFromGMO(db);
        }

        // Legacy path: use pre-processed Cartesian data + individual metadata pointers
        isaacsim::ros2::nodes::PointCloudMetadata metadata;
        metadata.intensityPtr = reinterpret_cast<float*>(db.inputs.intensityPtr());
        metadata.timestampPtr = reinterpret_cast<uint64_t*>(db.inputs.timestampPtr());
        metadata.emitterIdPtr = reinterpret_cast<uint32_t*>(db.inputs.emitterIdPtr());
        metadata.channelIdPtr = reinterpret_cast<uint32_t*>(db.inputs.channelIdPtr());
        metadata.materialIdPtr = reinterpret_cast<uint32_t*>(db.inputs.materialIdPtr());
        metadata.tickIdPtr = reinterpret_cast<uint32_t*>(db.inputs.tickIdPtr());
        metadata.hitNormalPtr = reinterpret_cast<GfVec3f*>(db.inputs.hitNormalPtr());
        metadata.velocityPtr = reinterpret_cast<GfVec3f*>(db.inputs.velocityPtr());
        metadata.objectIdPtr = reinterpret_cast<uint32_t*>(db.inputs.objectIdPtr());
        metadata.echoIdPtr = reinterpret_cast<uint8_t*>(db.inputs.echoIdPtr());
        metadata.tickStatePtr = reinterpret_cast<uint8_t*>(db.inputs.tickStatePtr());
        metadata.radialVelocityMSPtr = reinterpret_cast<float*>(db.inputs.radialVelocityMSPtr());

        if (db.inputs.cudaDeviceIndex() == -1)
        {
            if (db.inputs.dataPtr() != 0)
            {
                if (db.inputs.bufferSize() == 0)
                {
                    return false;
                }
                state.m_pub.getPointCloudMessage()->generateBuffer(
                    db.inputs.timeStamp(), state.m_pub.getFrameId(), db.inputs.bufferSize(), metadata.intensityPtr,
                    metadata.timestampPtr, metadata.emitterIdPtr, metadata.channelIdPtr, metadata.materialIdPtr,
                    metadata.tickIdPtr, metadata.hitNormalPtr, metadata.velocityPtr, metadata.objectIdPtr,
                    metadata.echoIdPtr, metadata.tickStatePtr, metadata.radialVelocityMSPtr);
                // Data is on host as ptr
                if (state.m_pub.getPointCloudMessage()->getOrderedFields().empty())
                {
                    // Direct copy when no metadata interleaving is needed
                    memcpy(state.m_pub.getPointCloudMessage()->getBufferPtr(),
                           reinterpret_cast<void*>(db.inputs.dataPtr()),
                           state.m_pub.getPointCloudMessage()->getTotalBytes());
                }
                else
                {
                    // Host interleave: fill buffer with xyz + metadata per point
                    isaacsim::ros2::nodes::fillPointCloudBufferHost(
                        reinterpret_cast<uint8_t*>(state.m_pub.getPointCloudMessage()->getBufferPtr()),
                        reinterpret_cast<const float3*>(db.inputs.dataPtr()),
                        state.m_pub.getPointCloudMessage()->getOrderedFields(),
                        state.m_pub.getPointCloudMessage()->getPointStep(),
                        state.m_pub.getPointCloudMessage()->getNumPoints());
                }
            }
            else
            {
                const size_t totalBytes = sizeof(GfVec3f) * db.inputs.data.size();
                if (totalBytes == 0)
                {
                    return false;
                }
                state.m_pub.getPointCloudMessage()->generateBuffer(
                    db.inputs.timeStamp(), state.m_pub.getFrameId(), totalBytes, metadata.intensityPtr,
                    metadata.timestampPtr, metadata.emitterIdPtr, metadata.channelIdPtr, metadata.materialIdPtr,
                    metadata.tickIdPtr, metadata.hitNormalPtr, metadata.velocityPtr, metadata.objectIdPtr,
                    metadata.echoIdPtr, metadata.tickStatePtr, metadata.radialVelocityMSPtr);
                // Data is on host as ogn data, copy from cpu
                {
                    memcpy(state.m_pub.getPointCloudMessage()->getBufferPtr(),
                           reinterpret_cast<const uint8_t*>(db.inputs.data.cpu().data()),
                           state.m_pub.getPointCloudMessage()->getTotalBytes());
                }
            }

            if (state.m_multithreadingDisabled)
            {
                CARB_PROFILE_ZONE(1, "[IsaacSim] Publish PCL");
                state.m_pub.send();
            }
            else
            {
                tasking->addTask(carb::tasking::Priority::eHigh, state.m_tasks,
                                 [&state]
                                 {
                                     CARB_PROFILE_ZONE(1, "[IsaacSim] Publish PCL Thread");
                                     state.m_pub.send();
                                 });
            }
        }
        else if (db.inputs.dataPtr() != 0)
        {
            const void* devicePtr = reinterpret_cast<const void*>(db.inputs.dataPtr());
            const size_t bufferSize = db.inputs.bufferSize();
            const double timestamp = db.inputs.timeStamp();
            const int cudaDeviceIndex = db.inputs.cudaDeviceIndex();

            if (state.m_multithreadingDisabled)
            {
                state.m_pub.publishFromDevice(devicePtr, bufferSize, timestamp, cudaDeviceIndex, metadata);
            }
            else
            {
                tasking->addTask(
                    carb::tasking::Priority::eHigh, state.m_tasks,
                    [&state, devicePtr, bufferSize, timestamp, cudaDeviceIndex, metadata]() mutable
                    { state.m_pub.publishFromDevice(devicePtr, bufferSize, timestamp, cudaDeviceIndex, metadata); });
            }
        }

        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishPointCloudDatabase::sPerInstanceState<OgnROS2PublishPointCloud>(nodeObj, instanceId);
        state.reset();
    }

    void reset() override
    {
        {
            CARB_PROFILE_ZONE(1, "[IsaacSim] wait for previous publish");
            m_tasks.wait();
        }
        m_pub.reset();
        Ros2Node::reset();
    }

private:
    isaacsim::ros2::nodes::PointCloudPublisher m_pub;

    carb::tasking::TaskGroup m_tasks;

    bool m_multithreadingDisabled = false;

    // Reusable buffers for GMO processing
    std::vector<float3> m_pcBuffer;
    std::vector<uint64_t> m_timestampBuffer;
};

REGISTER_OGN_NODE()

#ifdef _WIN32
#    pragma warning(pop)
#endif
