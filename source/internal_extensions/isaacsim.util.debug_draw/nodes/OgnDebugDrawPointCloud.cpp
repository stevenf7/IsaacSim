// SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

// Take a point cloud as input and display it in the scene.
#include <carb/InterfaceUtils.h>
#include <carb/profiler/Profile.h>

#include <boost/make_shared.hpp>
#include <boost/shared_ptr.hpp>
#include <isaacsim/core/includes/BaseResetNode.h>
#include <isaacsim/core/includes/Buffer.h>
#include <isaacsim/core/includes/ScopedCudaDevice.h>
#include <isaacsim/util/debug_draw/PrimitiveDrawingHelper.h>

#include <OgnDebugDrawPointCloudDatabase.h>
#include <iostream>

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
        float size = db.inputs.size();

        if (!db.inputs.testMode() && numVerts > 0)
        {
            state.m_pointDrawing->setVertices(input, numVerts);
            state.m_pointDrawing->setColor(*color);
            state.m_pointDrawing->setWidth(size);
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

    virtual void reset()
    {
        if (m_pointDrawing)
        {
            m_pointDrawing->clear();
            m_pointDrawing->draw();
        }
    }

private:
    std::shared_ptr<isaacsim::util::debug_draw::drawing::PrimitiveDrawingHelper> m_pointDrawing{ nullptr };
};

REGISTER_OGN_NODE()
} // debug_draw
} // isaac
} // omni
