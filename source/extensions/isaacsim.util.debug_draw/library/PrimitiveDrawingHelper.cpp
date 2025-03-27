// SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
#include <carb/renderer/RendererTypes.h>
#include <carb/scenerenderer/SceneRenderer.h>

#include <isaacsim/util/debug_draw/PrimitiveDrawingHelper.h>
// #include <tbb/parallel_for.h>

using namespace carb::scenerenderer;

namespace isaacsim
{
namespace util
{
namespace debug_draw
{
namespace drawing
{
PrimitiveDrawingHelper::PrimitiveDrawingHelper(omni::usd::UsdContext* usdContext,
                                               RenderingMode renderingMode,
                                               bool worldSpace,
                                               bool depthTest)
    : m_usdContext(usdContext),
      m_renderingMode(renderingMode),
      m_worldSpace(worldSpace),
      m_depthTest(depthTest),
      m_primitiveList(nullptr),
      m_dirty(false)
{
}
PrimitiveDrawingHelper::~PrimitiveDrawingHelper()
{
    clear();
    releaseList();
}

// Add a single vertex
void PrimitiveDrawingHelper::addVertex(const carb::Float3& position, const carb::ColorRgba& color, const float width)
{
    m_dirty = true;
    carb::scenerenderer::PrimitiveVertex point;
    point.position = position;
    point.width = width;
    point.color = color;
    m_vertices.push_back(point);
}
void PrimitiveDrawingHelper::addVertex(const carb::scenerenderer::PrimitiveVertex& vertex)
{
    m_dirty = true;
    m_vertices.push_back(vertex);
}
// Add a list of vertices
void PrimitiveDrawingHelper::addVertices(const std::vector<carb::Float3>& positions,
                                         const std::vector<carb::ColorRgba>& colors,
                                         const std::vector<float>& widths)
{
    m_dirty = true;
    carb::scenerenderer::PrimitiveVertex point;

    for (size_t i = 0; i < positions.size(); i++)
    {
        point.position = positions[i];
        point.width = widths[i];
        point.color = colors[i];
        m_vertices.push_back(point);
    }
}
// Add a list of vertices with constant color and width
void PrimitiveDrawingHelper::addVertices(const std::vector<carb::Float3>& positions,
                                         const carb::ColorRgba& color,
                                         float width)
{
    m_dirty = true;
    carb::scenerenderer::PrimitiveVertex point;
    size_t firstIndex = size();
    m_vertices.resize(firstIndex + positions.size());
    for (size_t i = 0; i < positions.size(); i++)
    {
        point.position = positions[i];
        point.width = width;
        point.color = color;
        m_vertices[firstIndex + i] = point;
    }
}

// set a list of vertices
void PrimitiveDrawingHelper::setVertices(const carb::Float3* p, size_t numPositions)
{
    if (m_vertices.size() != numPositions)
    {
        m_dirty = true;
    }
    m_vertices.resize(numPositions);
    for (int i = 0; i < static_cast<int>(numPositions); ++i)
    {
        m_vertices[i].position.x = p[i].x;
        m_vertices[i].position.y = p[i].y;
        m_vertices[i].position.z = p[i].z;
    }

    /*tbb::parallel_for(tbb::blocked_range<int>(0, numPositions),
                      [&](tbb::blocked_range<int> r)
                      {
                          for (int i = r.begin(); i < r.end(); ++i)
                          {
                              m_vertices[i].position = positions[i];
                              m_vertices[i].color = color;
                              m_vertices[i].width = width;
                          }
                      });*/
}

// transform the positions of vertices
void PrimitiveDrawingHelper::transformVertices(const double m[])
{
    int numPositions = static_cast<int>(m_vertices.size());
    for (int i = 0; i < numPositions; ++i)
    {
        m_vertices[i].position =
            carb::Float3{ static_cast<float>(m[0] * m_vertices[i].position.x + m[4] * m_vertices[i].position.y +
                                             m[8] * m_vertices[i].position.z + m[12]),
                          static_cast<float>(m[1] * m_vertices[i].position.x + m[5] * m_vertices[i].position.y +
                                             m[9] * m_vertices[i].position.z + m[13]),
                          static_cast<float>(m[2] * m_vertices[i].position.x + m[6] * m_vertices[i].position.y +
                                             m[10] * m_vertices[i].position.z + m[14]) };
    }
}

// set a constant color
void PrimitiveDrawingHelper::setColor(const carb::ColorRgba& color)
{
    int numPositions = static_cast<int>(m_vertices.size());
    for (int i = 0; i < numPositions; ++i)
    {
        m_vertices[i].color = color;
    }
}

// set a constant width
void PrimitiveDrawingHelper::setWidth(float width)
{
    int numPositions = static_cast<int>(m_vertices.size());
    for (int i = 0; i < numPositions; ++i)
    {
        m_vertices[i].width = width;
    }
}
void PrimitiveDrawingHelper::addVertices(const std::vector<carb::scenerenderer::PrimitiveVertex>& vertices)
{
    m_dirty = true;

    m_vertices.insert(m_vertices.end(), vertices.begin(), vertices.end());
}

void PrimitiveDrawingHelper::setVertices(const std::vector<carb::scenerenderer::PrimitiveVertex>& vertices)
{
    // avoid release/create of the primitive instance if the size is the same
    if (m_vertices.size() != vertices.size())
    {
        m_dirty = true;
    }
    m_vertices = vertices;
}

// render current vertices
void PrimitiveDrawingHelper::draw()
{
    if (m_dirty)
    {
        releaseList();
        createList();
    }
    if (!m_vertices.empty() && isValid())
    {

        carb::scenerenderer::PrimitiveListSettings settings = {};
        settings.width = 1.0f;
        settings.antialiasingWidth = 0;
        settings.fadeOutStartDistance = 1e10f;
        settings.fadeOutEndDistance = 1e10f;

        carb::scenerenderer::PrimitiveListInstance inst = {};
        inst.transform.m[0] = 1.f;
        inst.transform.m[1 + 4] = 1.f;
        inst.transform.m[2 + 8] = 1.f;
        inst.transform.m[3 + 12] = 1.f;

        m_usdContext->getSceneRenderer()->updatePrimitiveListSettings(
            m_usdContext->getSceneRendererContext(), m_primitiveList, settings);
        m_usdContext->getSceneRenderer()->updatePrimitiveListInstances(
            m_usdContext->getSceneRendererContext(), m_primitiveList, &inst, 0, 1, 1);
        m_usdContext->getSceneRenderer()->updatePrimitiveListVertices(m_usdContext->getSceneRendererContext(),
                                                                      m_primitiveList, m_vertices.data(), 0,
                                                                      m_vertices.size(), m_vertices.size());
    }
    else
    {
        releaseList();
    }
}
// clear data
void PrimitiveDrawingHelper::clear()
{
    m_vertices.clear();
}
size_t PrimitiveDrawingHelper::size()
{
    return m_vertices.size();
}

void PrimitiveDrawingHelper::createList()
{
    SceneId id = m_usdContext->getRendererScene();
    if (!m_primitiveList && id)
    {

        PrimitiveKind kind = m_renderingMode == RenderingMode::ePoints ? PrimitiveKind::ePoint : PrimitiveKind::eLine;
        carb::scenerenderer::PrimitiveListFlags flags = carb::scenerenderer::kPrimitiveListFlagNone;
        if (m_depthTest)
        {
            flags |= carb::scenerenderer::kPrimitiveListFlagDepthTest |
                     carb::scenerenderer::kPrimitiveListFlagDepthTestWrite;
        }
        if (m_worldSpace)
        {
            flags |= carb::scenerenderer::kPrimitiveListFlagWorldSpaceWidth;
        }
        m_primitiveList = m_usdContext->getSceneRenderer()->createPrimitiveList(
            m_usdContext->getSceneRendererContext(), id, kind, flags);
    }
}
void PrimitiveDrawingHelper::releaseList()
{
    if (isValid())
    {
        m_usdContext->getSceneRenderer()->destroyPrimitiveList(m_usdContext->getSceneRendererContext(), m_primitiveList);
        m_primitiveList = nullptr;
    }
}
bool PrimitiveDrawingHelper::isValid()
{
    return m_primitiveList && m_usdContext && m_usdContext->getSceneRenderer() &&
           m_usdContext->getSceneRendererContext() && m_usdContext->getRendererScene();
}
}
}
}
}
