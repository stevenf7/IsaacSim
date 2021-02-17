// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "Query.h"

#include <omni/kit/IEditor.h>
#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>


#if CARB_PLATFORM_WINDOWS
#    pragma warning(disable : 4996) // Disable "unsafe/insecure" warning
#endif


using namespace carb;


namespace omni
{
namespace isaac
{
namespace decals
{

static constexpr float kProjectionTol = 0.0005f;

static bool pointInTriangle(pxr::GfVec3f& normal,
                            const pxr::GfVec3f& point,
                            const pxr::GfVec3f& vert0,
                            const pxr::GfVec3f& vert1,
                            const pxr::GfVec3f& vert2)
{
    constexpr float kTriangleScale = 1.0f; // We should probably set this based on vertices

    constexpr float kSqScaledTol = kProjectionTol * kProjectionTol * kTriangleScale * kTriangleScale;

    using pxr::GfCross;
    using pxr::GfDot;
    using pxr::GfVec3f;

    // Find vectors for two edges sharing vert0
    const GfVec3f edge0 = vert1 - vert0;
    const GfVec3f edge2 = vert0 - vert2;

    // Calculate normal vector
    normal = GfCross(edge2, edge0);

    // Triangle constants
    const float n2 = GfDot(normal, normal);
    const float n2SqTol = n2 * kSqScaledTol;

    // Point relative to vert0
    const GfVec3f r0 = point - vert0;

    // Test that the point is inside edge0
    const float a0n = GfDot(normal, GfCross(edge0, r0));
    if (a0n < 0.0f && a0n * a0n > n2SqTol)
        return false;

    // Test that the point is inside edge2
    const float a2n = GfDot(normal, GfCross(edge2, r0));
    if (a2n < 0.0f && a2n * a2n > n2SqTol)
        return false;

    // Test that the point is inside edge1 (use total triangle area to calculate a1n)
    const float a1n = GfDot(normal, GfCross(vert2 - vert1, point - vert1));
    if (a1n < 0.0f && a1n * a1n > n2SqTol)
        return false;

    normal /= sqrt(n2);

    return true;
}

inline pxr::GfVec3f TransposeTransformDir(const pxr::GfMatrix4d& mat, const pxr::GfVec3f& vec)
{
    return pxr::GfVec3f((float)(vec[0] * mat[0][0] + vec[1] * mat[0][1] + vec[2] * mat[0][2]),
                        (float)(vec[0] * mat[1][0] + vec[1] * mat[1][1] + vec[2] * mat[1][2]),
                        (float)(vec[0] * mat[2][0] + vec[1] * mat[2][1] + vec[2] * mat[2][2]));
}


// SceneQueryHandler

class SceneQueryHandler : public ISceneQueryHandler
{
public:
    SceneQueryHandler(pxr::UsdStageWeakPtr stage);

    virtual void updateSurface(const char* primPath) override;
    virtual void updateQueryPosition(const carb::Float3& worldPosition) override;
    virtual void updateFromPicking() override;
    virtual const SceneQueryResult& getResult() const override;
    virtual void release() override;

private:
    struct Cache
    {
        Cache()
        {
        }

        bool isValid()
        {
            return path.length() > 0;
        }

        void invalidate()
        {
            path.clear();
            prim = pxr::UsdPrim();
            points.clear();
            indices.clear();
            counts.clear();
        }

        bool extractPrimMeshData();

        std::string path;
        pxr::UsdPrim prim;
        pxr::VtArray<pxr::GfVec3f> points;
        pxr::VtArray<int> indices;
        pxr::VtArray<int> counts;
    };

    bool updateCache(const char* path);

    bool findLocalGeometry(Float3& localPoistion, Float3& localNormal, const Float3& worldPosition);

    pxr::UsdStageWeakPtr m_stage;
    kit::IEditor* m_editor;
    Cache m_cache;
    SceneQueryResult m_result;
};

SceneQueryHandler::SceneQueryHandler(pxr::UsdStageWeakPtr stage) : m_stage(stage)
{
    carb::Framework* framework = carb::getFramework();
    m_editor = framework->acquireInterface<omni::kit::IEditor>();
}

void SceneQueryHandler::updateSurface(const char* primPath)
{
    const bool surfaceChanged = updateCache(primPath);
    m_result.surfacePrim = m_cache.prim;
    m_result.flags &= ~SceneQueryResult::eSurfaceChanged;
    if (surfaceChanged)
        m_result.flags |= SceneQueryResult::eSurfaceChanged;
}

void SceneQueryHandler::updateQueryPosition(const carb::Float3& worldPosition)
{
    const bool surfaceFound = findLocalGeometry(m_result.localPosition, m_result.localNormal, worldPosition);
    m_result.flags &= ~SceneQueryResult::eSurfaceFound;
    if (surfaceFound)
        m_result.flags |= SceneQueryResult::eSurfaceFound;
}

void SceneQueryHandler::updateFromPicking()
{
    Float3 worldPosition;
    if (m_editor->getPickedWorldPosition(worldPosition))
    {
        updateSurface(m_editor->getQueriedPath());
        updateQueryPosition(worldPosition);
    }
    else
    {
        m_result.flags = updateCache(nullptr) ? SceneQueryResult::eSurfaceChanged : 0;
        m_result.surfacePrim = pxr::UsdPrim();
    }

    m_editor->requestPicking(); // Renew request for next frame
}

const SceneQueryResult& SceneQueryHandler::getResult() const
{
    return m_result;
}

void SceneQueryHandler::release()
{
    delete this;
}

bool SceneQueryHandler::updateCache(const char* path)
{
    const char* safePath = path != nullptr ? path : "";

    if (safePath == m_cache.path)
        return false;

    if (m_stage != nullptr)
    {
        m_cache.path = safePath;
        m_cache.prim = m_stage->GetPrimAtPath(pxr::SdfPath(m_cache.path));
        if (m_cache.extractPrimMeshData())
            return true;
    }

    m_cache.invalidate();
    return true;
}

bool SceneQueryHandler::findLocalGeometry(Float3& localPosition, Float3& localNormal, const Float3& worldPosition)
{
    if (!m_cache.isValid())
        return false;

    double det = 0.0;
    const pxr::GfMatrix4d worldToLocal = usd::UsdUtils::getWorldTransformMatrix(m_cache.prim).GetInverse(&det);
    if (det == 0.0)
        return false;

    pxr::GfVec3f localPoint =
        worldToLocal.TransformAffine(pxr::GfVec3f(worldPosition.x, worldPosition.y, worldPosition.z));

    const int* indices = m_cache.indices.data();
    const pxr::GfVec3f* vertices = m_cache.points.data();

    float maxSignedDistance = -FLT_MAX;

    for (int count : m_cache.counts)
    {
        if (count == 0)
            continue;
        const int i0 = *indices++;
        if (count == 1)
            continue;
        int i1 = *indices++;
        for (int tri = 0; tri < count - 2; ++tri)
        {
            const int i2 = *indices++;
            pxr::GfVec3f triangleNormal;
            if (pointInTriangle(triangleNormal, localPoint, vertices[i0], vertices[i1], vertices[i2]))
            {
                const float signedDistance = pxr::GfDot(localPoint - vertices[i0], triangleNormal);
                if (signedDistance > maxSignedDistance)
                {
                    maxSignedDistance = signedDistance;
                    // Project onto triangle plane
                    const pxr::GfVec3f projLocalPoint = localPoint - triangleNormal * signedDistance;
                    localPosition = { projLocalPoint[0], projLocalPoint[1], projLocalPoint[2] };
                    localNormal = { triangleNormal[0], triangleNormal[1], triangleNormal[2] };
                }
            }
            i1 = i2;
        }
    }

    return maxSignedDistance > -FLT_MAX;
}

bool SceneQueryHandler::Cache::extractPrimMeshData()
{
    using namespace pxr;

    if (!prim.IsValid())
        return false;

    // GeomMesh, just grab buffers
    if (prim.IsA<UsdGeomMesh>())
    {
        UsdGeomMesh mesh(prim);
        pxr::UsdAttribute pointsAttr = mesh.GetPointsAttr();
        if (!pointsAttr.Get<pxr::VtArray<pxr::GfVec3f>>(&points))
            return false;

        pxr::UsdAttribute indicesAttr = mesh.GetFaceVertexIndicesAttr();
        if (!indicesAttr.Get<pxr::VtArray<int>>(&indices))
            return false;

        pxr::UsdAttribute countsAttr = mesh.GetFaceVertexCountsAttr();
        if (!countsAttr.Get<pxr::VtArray<int>>(&counts))
            return false;

        return true;
    }

    if (!prim.IsA<UsdGeomGprim>())
        return false;

    // Handle other GeomGprims
    if (prim.IsA<UsdGeomCube>())
    {
        const UsdAttribute sizeAttr = UsdGeomCube(prim).GetSizeAttr();
        double size;
        if (!sizeAttr.Get<double>(&size))
            return false;
        const float s = (float)(0.5 * size);
        points = { { -s, -s, -s }, { s, -s, -s }, { -s, s, -s }, { s, s, -s },
                   { -s, -s, s },  { s, -s, s },  { -s, s, s },  { s, s, s } };
        indices = { 0, 4, 6, 2, 1, 3, 7, 5, 0, 1, 5, 4, 2, 6, 7, 3, 0, 2, 3, 1, 4, 5, 7, 6 };
        counts = { 4, 4, 4, 4, 4, 4 };
    }
    else if (prim.IsA<UsdGeomSphere>())
    {
        return false;
    }
    else if (prim.IsA<UsdGeomCapsule>())
    {
        return false;
    }
    else if (prim.IsA<UsdGeomCylinder>())
    {
        return false;
    }
    else if (prim.IsA<UsdGeomCone>())
    {
        return false;
    }

    return true;
}

// Global create function
ISceneQueryHandler* createSceneQueryHandler(pxr::UsdStageWeakPtr stage)
{
    if (stage == nullptr)
        return nullptr;

    return new SceneQueryHandler(stage);
}

} // namespace omni
} // namespace isaac
} // namespace decals
