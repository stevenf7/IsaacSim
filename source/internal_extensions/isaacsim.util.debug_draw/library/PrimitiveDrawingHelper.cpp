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

// Define the private vertex data structure
struct PrimitiveDrawingHelper::VertexData
{
    std::vector<PrimitiveVertex> vertices;
    SceneId lastSceneId = nullptr;
};

PrimitiveDrawingHelper::PrimitiveDrawingHelper(omni::usd::UsdContext* usdContext,
                                               RenderingMode renderingMode,
                                               bool worldSpace,
                                               bool depthTest)
    : m_usdContext(usdContext),
      m_renderingMode(renderingMode),
      m_worldSpace(worldSpace),
      m_depthTest(depthTest),
      m_dirty(false),
      m_vertexData(new VertexData()),
      m_primitiveList(nullptr)
{
}

PrimitiveDrawingHelper::~PrimitiveDrawingHelper()
{
    clear();
    _releaseList();
}

// Add a single vertex
void PrimitiveDrawingHelper::addVertex(const carb::Float3& position, const carb::ColorRgba& color, const float width)
{
    m_dirty = true;
    PrimitiveVertex point;
    point.position = position;
    point.width = width;
    point.color = color;
    m_vertexData->vertices.push_back(point);
}

// Add a list of vertices
void PrimitiveDrawingHelper::addVertices(const std::vector<carb::Float3>& positions,
                                         const std::vector<carb::ColorRgba>& colors,
                                         const std::vector<float>& widths)
{
    m_dirty = true;
    PrimitiveVertex point;
    m_vertexData->vertices.reserve(m_vertexData->vertices.size() + positions.size());

    for (size_t i = 0; i < positions.size(); i++)
    {
        point.position = positions[i];
        point.width = widths[i];
        point.color = colors[i];
        m_vertexData->vertices.push_back(point);
    }
}

// Add a list of vertices with constant color and width
void PrimitiveDrawingHelper::addVertices(const std::vector<carb::Float3>& positions,
                                         const carb::ColorRgba& color,
                                         float width)
{
    m_dirty = true;
    PrimitiveVertex point;
    size_t firstIndex = size();
    m_vertexData->vertices.resize(firstIndex + positions.size());
    for (size_t i = 0; i < positions.size(); i++)
    {
        point.position = positions[i];
        point.width = width;
        point.color = color;
        m_vertexData->vertices[firstIndex + i] = point;
    }
}

// set a list of vertices
void PrimitiveDrawingHelper::setVertices(const carb::Float3* p, size_t numPositions)
{
    m_dirty = true;
    if (m_vertexData->vertices.size() != numPositions)
    {
        // Ensure capacity or just let resize handle it.
        // vector::resize might realloc.
    }
    m_vertexData->vertices.resize(numPositions);
    for (size_t i = 0; i < numPositions; ++i)
    {
        m_vertexData->vertices[i].position.x = p[i].x;
        m_vertexData->vertices[i].position.y = p[i].y;
        m_vertexData->vertices[i].position.z = p[i].z;
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
    m_dirty = true;
    size_t numPositions = m_vertexData->vertices.size();
    for (size_t i = 0; i < numPositions; ++i)
    {
        m_vertexData->vertices[i].position = carb::Float3{
            static_cast<float>(m[0] * m_vertexData->vertices[i].position.x + m[4] * m_vertexData->vertices[i].position.y +
                               m[8] * m_vertexData->vertices[i].position.z + m[12]),
            static_cast<float>(m[1] * m_vertexData->vertices[i].position.x + m[5] * m_vertexData->vertices[i].position.y +
                               m[9] * m_vertexData->vertices[i].position.z + m[13]),
            static_cast<float>(m[2] * m_vertexData->vertices[i].position.x + m[6] * m_vertexData->vertices[i].position.y +
                               m[10] * m_vertexData->vertices[i].position.z + m[14])
        };
    }
}

// set a constant color
void PrimitiveDrawingHelper::setColor(const carb::ColorRgba& color)
{
    m_dirty = true;
    size_t numPositions = m_vertexData->vertices.size();
    for (size_t i = 0; i < numPositions; ++i)
    {
        m_vertexData->vertices[i].color = color;
    }
}

// set a constant width
void PrimitiveDrawingHelper::setWidth(float width)
{
    m_dirty = true;
    size_t numPositions = m_vertexData->vertices.size();
    for (size_t i = 0; i < numPositions; ++i)
    {
        m_vertexData->vertices[i].width = width;
    }
}

// render current vertices
void PrimitiveDrawingHelper::draw()
{
    SceneId currentSceneId = m_usdContext->getRendererScene();
    if (m_vertexData->lastSceneId != currentSceneId)
    {
        _releaseList();
        m_vertexData->lastSceneId = currentSceneId;
        m_dirty = true;
    }

    if (!m_primitiveList)
    {
        _createList();
        // If we just created the list, we need to push data
        m_dirty = true;
    }

    if (!m_vertexData->vertices.empty() && _isValid())
    {
        if (m_dirty)
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
            m_usdContext->getSceneRenderer()->updatePrimitiveListVertices(
                m_usdContext->getSceneRendererContext(), m_primitiveList, m_vertexData->vertices.data(), 0,
                m_vertexData->vertices.size(), m_vertexData->vertices.size());

            m_dirty = false;
        }
    }
    else
    {
        _releaseList();
    }
}

// clear data
void PrimitiveDrawingHelper::clear()
{
    m_vertexData->vertices.clear();
}

size_t PrimitiveDrawingHelper::size()
{
    return m_vertexData->vertices.size();
}

void PrimitiveDrawingHelper::_createList()
{
    SceneId id = m_usdContext->getRendererScene();
    if (!m_primitiveList && id)
    {
        PrimitiveKind kind = (m_renderingMode == RenderingMode::ePoints) ? PrimitiveKind::ePoint : PrimitiveKind::eLine;
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

void PrimitiveDrawingHelper::_releaseList()
{
    if (_isValid())
    {
        m_usdContext->getSceneRenderer()->destroyPrimitiveList(m_usdContext->getSceneRendererContext(), m_primitiveList);
        m_primitiveList = nullptr;
    }
}

bool PrimitiveDrawingHelper::_isValid()
{
    return m_primitiveList && m_usdContext && m_usdContext->getSceneRenderer() &&
           m_usdContext->getSceneRendererContext() && m_usdContext->getRendererScene();
}
}
}
}
}
