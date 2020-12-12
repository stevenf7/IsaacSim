// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Framework.h>

namespace omni
{
namespace isaac
{
namespace decals
{

class Instancer
{
public:
    Instancer();
    ~Instancer();

    bool init(pxr::UsdStageWeakPtr stage, const pxr::SdfPath& path, uint32_t maxInstanceCount);

    bool setMeshes(const pxr::SdfPathVector& meshPaths);

    bool fillFromPrim(pxr::UsdPrim prim);

    uint32_t getMaxInstanceCount() const
    {
        return (uint32_t)m_meshIndices.size();
    }

    void setInstance(uint32_t instanceIndex, uint32_t meshIndex, const pxr::GfMatrix4d& localTransform);

    void sendBuffers(bool forceSend = false);

    pxr::UsdPrim getPrim()
    {
        return m_instancer.GetPrim();
    }

protected:
    void allocate(uint32_t maxInstanceCount, bool clear = false);

private:
    // Buffers
    pxr::VtArray<int> m_meshIndices;
    // BRG - should switch to full matrix if possible
    pxr::VtArray<pxr::GfVec3f> m_scales;
    pxr::VtArray<pxr::GfQuath> m_orientations;
    pxr::VtArray<pxr::GfVec3f> m_positions;
    bool m_buffersChanged;

    // Stage objects
    pxr::UsdGeomPointInstancer m_instancer;
};

} // namespace omni
} // namespace isaac
} // namespace decals
