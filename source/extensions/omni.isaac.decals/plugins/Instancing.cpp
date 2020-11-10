// Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "Instancing.h"

using namespace carb;

#if CARB_PLATFORM_WINDOWS
#    pragma warning(disable : 4244) // Conversion from double to float / int to float
#endif

#include <carb/logging/Log.h>


namespace omni
{
namespace isaac
{
namespace decals
{

static const pxr::TfToken sInstanceTransformToken("instanceTransform");

Instancer::Instancer() : m_buffersChanged(true)
{
}

Instancer::~Instancer()
{
}

bool Instancer::init(pxr::UsdStageWeakPtr stage, const pxr::SdfPath& path, uint32_t maxInstanceCount)
{
    if (stage == nullptr || maxInstanceCount == 0)
        return false;

    allocate(maxInstanceCount, true);

    if (stage->GetPrimAtPath(path).IsValid())
        return false;

    m_instancer = pxr::UsdGeomPointInstancer::Define(stage, path);

    return true;
}

bool Instancer::setMeshes(const pxr::SdfPathVector& meshPaths)
{
    return m_instancer.GetPrototypesRel().SetTargets(meshPaths);
}

bool Instancer::fillFromPrim(pxr::UsdPrim prim)
{
    if (!prim.IsValid())
        return false;

    m_instancer = pxr::UsdGeomPointInstancer(prim);

    m_instancer.GetProtoIndicesAttr().Get(&m_meshIndices);
    m_instancer.GetPositionsAttr().Get(&m_positions);
    m_instancer.GetOrientationsAttr().Get(&m_orientations);
    m_instancer.GetScalesAttr().Get(&m_scales);

    CARB_ASSERT(m_positions.size() == m_meshIndices.size() && m_orientations.size() == m_meshIndices.size() &&
                m_scales.size() == m_meshIndices.size());

    return true;
}

void Instancer::setInstance(uint32_t instanceIndex, uint32_t meshIndex, const pxr::GfMatrix4d& localTransform)
{
    CARB_ASSERT(instanceIndex < m_meshIndices.size());
    if (instanceIndex >= m_meshIndices.size())
        return;

    m_meshIndices[instanceIndex] = meshIndex;

    pxr::GfMatrix3d m(localTransform[0][0], localTransform[0][1], localTransform[0][2], localTransform[1][0],
                      localTransform[1][1], localTransform[1][2], localTransform[2][0], localTransform[2][1],
                      localTransform[2][2]);

    // Not handling non-uniform scales
    m_scales[instanceIndex] =
        pxr::GfVec3f((float)((pxr::GfVec3d*)m[0])->Normalize(), (float)((pxr::GfVec3d*)m[1])->Normalize(),
                     (float)((pxr::GfVec3d*)m[2])->Normalize());

    const pxr::GfQuaternion quat = m.ExtractRotationQuaternion();
    const pxr::GfVec3d imag = quat.GetImaginary();
    m_orientations[instanceIndex] =
        pxr::GfQuath(quat.GetReal(), pxr::GfVec3h((pxr::GfHalf)imag[0], (pxr::GfHalf)imag[1], (pxr::GfHalf)imag[2]));

    m_positions[instanceIndex] = pxr::GfVec3f(localTransform.GetRow3(3));

    m_buffersChanged = true;
}

void Instancer::sendBuffers(bool forceSend /* = false */)
{
    if (m_buffersChanged || forceSend)
    {
        m_instancer.GetProtoIndicesAttr().Set(m_meshIndices);
        m_instancer.GetPositionsAttr().Set(m_positions);
        m_instancer.GetOrientationsAttr().Set(m_orientations);
        m_instancer.GetScalesAttr().Set(m_scales);
        m_buffersChanged = false;
    }
}

void Instancer::allocate(uint32_t maxInstanceCount, bool clear /* = false*/)
{
    const size_t oldSize = !clear ? m_meshIndices.size() : 0;
    if (!clear && oldSize >= maxInstanceCount)
        return;

    m_meshIndices.resize(maxInstanceCount);
    std::fill(m_meshIndices.begin() + oldSize, m_meshIndices.end(), 0);

    m_scales.resize(maxInstanceCount);
    std::fill(m_positions.begin() + oldSize, m_positions.end(), pxr::GfVec3f(0.0f));

    m_orientations.resize(maxInstanceCount);
    std::fill(m_orientations.begin() + oldSize, m_orientations.end(), pxr::GfQuath(1.0f));

    m_positions.resize(maxInstanceCount);
    std::fill(m_scales.begin() + oldSize, m_scales.end(), pxr::GfVec3f(0.0f));

    m_buffersChanged = true;
}

} // namespace omni
} // namespace isaac
} // namespace decals
