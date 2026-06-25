// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

// Take a point cloud as input and display it in the scene.
#include <carb/InterfaceUtils.h>
#include <carb/profiler/Profile.h>

#include <isaacsim/core/includes/BaseResetNode.h>
#include <isaacsim/core/includes/Buffer.h>
#include <isaacsim/core/includes/ScopedCudaDevice.h>
#include <isaacsim/util/debug_draw/PrimitiveDrawingHelper.h>

#include <OgnDebugDrawPointCloudDatabase.h>

namespace isaacsim
{
namespace util
{
namespace debug_draw
{

class OgnDebugDrawPointCloud : public isaacsim::core::includes::BaseResetNode
{
public:
    static void setPointDrawing(isaacsim::util::debug_draw::OgnDebugDrawPointCloud& state)
    {
        state.m_pointDrawing = std::make_shared<drawing::PrimitiveDrawingHelper>(
            omni::usd::UsdContext::getContext(), drawing::PrimitiveDrawingHelper::RenderingMode::ePoints,
            true /*World Coords*/);
    }

    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {

        auto& state = OgnDebugDrawPointCloudDatabase::sPerInstanceState<OgnDebugDrawPointCloud>(nodeObj, instanceId);
        setPointDrawing(state);
    }


    static bool compute(OgnDebugDrawPointCloudDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Debug Draw Point Cloud");

        carb::Float3* input;
        void* dataPtr = reinterpret_cast<void*>(db.inputs.dataPtr());
        int cudaDeviceIndex = db.inputs.cudaDeviceIndex();
        size_t numVerts = db.inputs.bufferSize() / sizeof(carb::Float3);
        isaacsim::core::includes::HostBufferBase<carb::Float3> inputBuffer;
        if (cudaDeviceIndex >= 0)
        {
            isaacsim::core::includes::ScopedDevice device(cudaDeviceIndex);
            if (numVerts > inputBuffer.size())
            {
                inputBuffer.resize(numVerts);
            }
            CUDA_CHECK(cudaMemcpyAsync(inputBuffer.data(), dataPtr, db.inputs.bufferSize(), cudaMemcpyDeviceToHost,
                                       (cudaStream_t)db.inputs.cudaStream()));
            CUDA_CHECK(cudaStreamSynchronize((cudaStream_t)db.inputs.cudaStream()));
            input = inputBuffer.data();
        }
        else
        {
            input = reinterpret_cast<carb::Float3*>(dataPtr);
        }

        auto& state = db.perInstanceState<OgnDebugDrawPointCloud>();
        if (!state.m_pointDrawing.get())
        {
            setPointDrawing(state);
        }
        if (!input)
        {
            if (numVerts)
            {
                db.logError("DebugDrawPointCloud Buffer is invalid, but should have %d vertices.", numVerts);
            }

            state.m_pointDrawing->clear();
            state.m_pointDrawing->draw();
            return false;
        }


        const carb::ColorRgba* color = (const carb::ColorRgba*)db.inputs.color().data();
        // Optional per-point colors supplied as a host buffer pointer, one RGBA entry per vertex
        const pxr::GfVec4f* colors = reinterpret_cast<const pxr::GfVec4f*>(db.inputs.colorsPtr());
        const size_t numColors = db.inputs.colorsBufferSize() / sizeof(pxr::GfVec4f);
        float size = db.inputs.size();

        if (!db.inputs.testMode() && numVerts > 0)
        {
            // Use per-point colors when one is supplied per vertex, otherwise the single flat color
            if (colors && numColors == numVerts)
            {
                // Reuse the persistent per-instance buffers so their capacity is retained across
                // steps and the per-point arrays are not reallocated every compute().
                state.m_pointPositions.assign(input, input + numVerts);
                state.m_pointColors.clear();
                state.m_pointWidths.clear();
                state.m_pointColors.reserve(numVerts);
                state.m_pointWidths.reserve(numVerts);
                for (size_t index = 0; index < numVerts; ++index)
                {
                    const pxr::GfVec4f& pointColor = colors[index];
                    state.m_pointColors.emplace_back(
                        carb::ColorRgba{ pointColor[0], pointColor[1], pointColor[2], pointColor[3] });
                    state.m_pointWidths.emplace_back(size);
                }
                state.m_pointDrawing->clear();
                state.m_pointDrawing->addVertices(state.m_pointPositions, state.m_pointColors, state.m_pointWidths);
            }
            else
            {
                state.m_pointDrawing->setVertices(input, numVerts);
                state.m_pointDrawing->setColor(*color);
                state.m_pointDrawing->setWidth(size);
            }

            // if there is no transform input, then don't use it.
            auto& nodeObj = db.abi_node();
            const AttributeObj attr = nodeObj.iNode->getAttributeByToken(nodeObj, inputs::transform.m_token);
            if (db.inputs.doTransform() && attr.iAttribute->getUpstreamConnectionCount(attr))
            {
                state.m_pointDrawing->transformVertices(db.inputs.transform().data());
            }
        }
        else
        {
            state.m_pointDrawing->clear();
        }
        state.m_pointDrawing->draw();
        return true;
    }

    void reset() override
    {
        if (m_pointDrawing)
        {
            m_pointDrawing->clear();
            m_pointDrawing->draw();
        }
    }

private:
    std::shared_ptr<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper> m_pointDrawing{ nullptr };

    // Persistent per-point buffers reused across compute() calls to avoid per-step reallocation.
    std::vector<carb::Float3> m_pointPositions;
    std::vector<carb::ColorRgba> m_pointColors;
    std::vector<float> m_pointWidths;
};

REGISTER_OGN_NODE()
}
}
}
