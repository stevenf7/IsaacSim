// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
// clang-format on

#include "Drawing.h"

#include "Instancing.h"

#include <carb/logging/Log.h>

#include <map>
#include <vector>

#if CARB_PLATFORM_WINDOWS
#    pragma warning(disable : 4996) // Disable "unsafe/insecure" warning
#    pragma warning(disable : 4244) // Conversion from double to float / int to float
#endif


using namespace carb;

#define DECAL_NODE_ID "omni_isaac_decals"
#define DECAL_NODE_VER "1_0"

#define DECAL_NAME DECAL_NODE_ID "_" DECAL_NODE_VER
#define DECAL_MESH_CONTAINER_PATH "/" DECAL_NAME

typedef uint32_t (*GrowthFunction)(uint32_t);

#define USE_DEBUG_COLORS 0

namespace omni
{
namespace isaac
{
namespace decals
{

const static pxr::TfToken sCurrentInstanceIndexToken("currentInstanceIndex");
const static pxr::TfToken sInstancedMeshesToken("instancedMeshes");


static inline uint32_t rgbVecToVal(const pxr::GfVec3f& rgb)
{
    uint32_t val = 0;
    for (int i = 0; i < 3; ++i)
        val = val << 8 | (uint32_t)std::max(std::min(rgb[i] * 255, 255.0f), 0.0f);
    return val;
}

static inline pxr::GfVec3f rgbValToVec(uint32_t val)
{
    return pxr::GfVec3f(
        (float)((val >> 16) & 0xFF) / 255.0f, (float)((val >> 8) & 0xFF) / 255.0f, (float)(val & 0xFF) / 255.0f);
}

static inline bool createMeshClass(pxr::UsdGeomMesh& mesh, pxr::UsdStageWeakPtr& stage, const char* name)
{
    const pxr::SdfPath containerPath(DECAL_MESH_CONTAINER_PATH);
    pxr::UsdPrim containerPrim = stage->GetPrimAtPath(containerPath);
    if (!containerPrim.IsValid())
    {
        pxr::UsdGeomScope container = pxr::UsdGeomScope::Define(stage, containerPath);
        container.MakeInvisible();
        container.GetPrim().CreateRelationship(sInstancedMeshesToken);
    }

    const std::string meshClassPathStr = std::string(DECAL_MESH_CONTAINER_PATH) + "/" + name;
    const pxr::SdfPath meshClassPath(meshClassPathStr);
    pxr::UsdPrim prim = stage->GetPrimAtPath(meshClassPath);
    if (prim.IsValid())
    {
        mesh = pxr::UsdGeomMesh(prim);
        return false;
    }

    prim = stage->CreateClassPrim(meshClassPath);
    mesh = pxr::UsdGeomMesh::Define(stage, meshClassPath);

    return true;
}

static inline void fillMeshClass(pxr::UsdGeomMesh& mesh,
                                 const std::vector<pxr::GfVec3f>& points,
                                 const std::vector<pxr::GfVec3f>& normals,
                                 const std::vector<int>& indices,
                                 const std::vector<int>& vertexCounts)
{
    // Fill in VtArrays
    pxr::VtArray<int> vertexCountsVt;
    vertexCountsVt.assign(vertexCounts.begin(), vertexCounts.end());
    pxr::VtArray<int> vertexIndicesVt;
    vertexIndicesVt.assign(indices.begin(), indices.end());
    pxr::VtArray<pxr::GfVec3f> pointArrayVt;
    pointArrayVt.assign(points.begin(), points.end());
    pxr::VtArray<pxr::GfVec3f> normalsVt;
    normalsVt.assign(normals.begin(), normals.end());

    mesh.GetFaceVertexCountsAttr().Set(vertexCountsVt);
    mesh.GetFaceVertexIndicesAttr().Set(vertexIndicesVt);
    mesh.GetPointsAttr().Set(pointArrayVt);
    mesh.GetDoubleSidedAttr().Set(true);
    mesh.GetNormalsAttr().Set(normalsVt);
    mesh.GetDisplayColorAttr().Set(pxr::VtArray<pxr::GfVec3f>(1, pxr::GfVec3f(1.0f)));
}

struct MeshClassCreate
{
    virtual const char* name() const = 0;
    virtual pxr::UsdGeomMesh create(pxr::UsdStageWeakPtr stage) = 0;
};

struct MeshClassCreateTriangle : public MeshClassCreate
{
    const char* name() const override
    {
        return "triangle";
    }

    pxr::UsdGeomMesh create(pxr::UsdStageWeakPtr stage) override
    {
        pxr::UsdGeomMesh mesh;
        if (createMeshClass(mesh, stage, name()))
        {
            const std::vector<pxr::GfVec3f> points = { { -1.0f, -1.0f, 0.0f },
                                                       { 1.0f, -1.0f, 0.0f },
                                                       { -1.0f, 1.0f, 0.0f } };
            const std::vector<pxr::GfVec3f> normals(3, { 0, 0, 1 });
            const std::vector<int> indices = { 0, 1, 2 };
            const std::vector<int> vertexCounts(1, 3);

            // Fill the mesh
            fillMeshClass(mesh, points, normals, indices, vertexCounts);
        }
        return mesh;
    }
};

struct MeshClassCreateSquare : public MeshClassCreate
{
    const char* name() const override
    {
        return "square";
    }

    pxr::UsdGeomMesh create(pxr::UsdStageWeakPtr stage) override
    {
        pxr::UsdGeomMesh mesh;
        if (createMeshClass(mesh, stage, name()))
        {
            const std::vector<pxr::GfVec3f> points = {
                { -1.0f, -1.0f, 0.0f }, { 1.0f, -1.0f, 0.0f }, { 1.0f, 1.0f, 0.0f }, { -1.0f, 1.0f, 0.0f }
            };
            const std::vector<pxr::GfVec3f> normals(4, { 0, 0, 1 });
            const std::vector<int> indices = { 0, 1, 2, 3 };
            const std::vector<int> vertexCounts(1, 4);

            // Fill the mesh
            fillMeshClass(mesh, points, normals, indices, vertexCounts);
        }
        return mesh;
    }
};


struct MeshClassCreateCircle : public MeshClassCreate
{
    MeshClassCreateCircle(int pointCount = 64) : m_pointCount(pointCount)
    {
    }

    const char* name() const override
    {
        return "circle";
    }

    pxr::UsdGeomMesh create(pxr::UsdStageWeakPtr stage) override
    {
        pxr::UsdGeomMesh mesh;
        if (createMeshClass(mesh, stage, name()))
        {
            const std::vector<pxr::GfVec3f> normals(m_pointCount, { 0, 0, 1 });
            const std::vector<int> vertexCounts(1, m_pointCount);

            std::vector<pxr::GfVec3f> points(m_pointCount);
            std::vector<int> indices(m_pointCount);

            for (int n = 0; n < m_pointCount; ++n)
            {
                const float theta = n * 6.28318531f / m_pointCount;
                points[n] = pxr::GfVec3f(std::cos(theta), std::sin(theta), 0.0f);
                indices[n] = n;
            }

            // Fill the mesh
            fillMeshClass(mesh, points, normals, indices, vertexCounts);
        }
        return mesh;
    }

private:
    int m_pointCount;
};

static pxr::GfMatrix4d createPointNormalTm(const pxr::GfVec3f& point, const pxr::GfVec3f& z)
{
    int i_min = (int)(std::abs(z[1]) < std::abs(z[0]));
    if (std::abs(z[2]) < std::abs(z[i_min]))
        i_min = 2;

    pxr::GfVec3d u(0.0f);
    u[i_min] = 1.0f;

    pxr::GfVec3d y = pxr::GfCross(z, u);
    y.Normalize();

    pxr::GfMatrix4d tm;
    tm.SetRow3(0, pxr::GfCross(y, z));
    tm.SetRow3(1, y);
    tm.SetRow3(2, z);
    tm.SetRow3(3, point);

    return tm;
}

static pxr::GfMatrix4d calculateQuadTransform(float width,
                                              const pxr::GfVec3f& length,
                                              const pxr::GfVec3f& normal,
                                              const pxr::GfVec3f& pos,
                                              bool lengthAlongX = true)
{
    // Create local-to-world
    const pxr::GfVec3d z = normal;
    pxr::GfVec3d x, y;
    if (lengthAlongX)
    {
        x = 0.5 * length; // Scale local x for length
        y = 0.5 * width * pxr::GfCross(z, x).GetNormalized(); // Scale local y for width
    }
    else
    {
        y = 0.5 * length; // Scale local y for length
        x = 0.5 * width * pxr::GfCross(y, z).GetNormalized(); // Scale local x for width
    }
    return pxr::GfMatrix4d(
        x[0], x[1], x[2], 0.0, y[0], y[1], y[2], 0.0, z[0], z[1], z[2], 0.0, pos[0], pos[1], pos[2], 1.0);
}


// Data for {DECAL_NODE_ID}_{DECAL_NODE_VER} child instancer node
class DecalGraphics : public Instancer
{
public:
    DecalGraphics(uint32_t initialBufferSize, GrowthFunction bufferGrowthFn);

    bool init(pxr::UsdPrim surfacePrim, const pxr::SdfPathVector& meshes);
    bool term();

    bool isInitialized()
    {
        return getPrim().IsValid();
    }

    void draw();

    void drawDot(uint32_t meshIndex, const pxr::GfVec3f& normal, const pxr::GfVec3f& position, float width, float offset);

    void drawLine(uint32_t meshIndex,
                  const pxr::GfVec3f& normal,
                  const pxr::GfVec3f& from,
                  const pxr::GfVec3f& to,
                  float width,
                  float offset);

    void drawRtTriangle(uint32_t meshIndex,
                        bool rightAltitude,
                        const pxr::GfVec3f& normal,
                        const pxr::GfVec3f& position,
                        const pxr::GfVec3f& altitude,
                        float width,
                        float offset);

    void advanceStroke()
    {
        m_instIndexPrev = m_instIndexCurr;
    }

    void resetStroke()
    {
        m_instIndexCurr = m_instIndexPrev;
        m_updateNeeded = true;
    }

private:
    inline void setNextInstance(uint32_t meshIndex, const pxr::GfMatrix4d& localTransform);
    inline uint32_t growInstanceBuffers();

    bool create(pxr::UsdStageWeakPtr stage, pxr::SdfPath path);
    bool load(pxr::UsdPrim decalPrim);

    // Graphics
    uint32_t m_initialBufferSize;
    GrowthFunction m_bufferGrowthFn;
    uint32_t m_instIndexPrev;
    uint32_t m_instIndexCurr;
    bool m_updateNeeded;

    static constexpr pxr::GfVec3f kDefaultColor = pxr::GfVec3f(1.0f);
};

DecalGraphics::DecalGraphics(uint32_t initialBufferSize, GrowthFunction bufferGrowthFn)
    : m_initialBufferSize(initialBufferSize),
      m_bufferGrowthFn(bufferGrowthFn),
      m_instIndexPrev(0),
      m_instIndexCurr(0),
      m_updateNeeded(false)
{
}

bool DecalGraphics::init(pxr::UsdPrim surfacePrim, const pxr::SdfPathVector& meshes)
{
    if (!surfacePrim.IsValid())
        return false;

    pxr::UsdStageWeakPtr stage = surfacePrim.GetStage();

    const std::string decalPathStr = surfacePrim.GetPath().GetString() + "/" + DECAL_NAME;
    const pxr::SdfPath decalPath(decalPathStr);

    pxr::UsdPrim decalPrim = stage->GetPrimAtPath(decalPath);

    if (!decalPrim.IsValid())
        create(stage, decalPath);
    else
        load(decalPrim);

    setMeshes(meshes);

    return getPrim().IsValid();
}

bool DecalGraphics::term()
{
    return true;
}

void DecalGraphics::draw()
{
    pxr::UsdPrim instancerPrim = getPrim();

    if (!isInitialized())
        return;

    if (m_updateNeeded)
    {
        getPrim().GetAttribute(sCurrentInstanceIndexToken).Set(m_instIndexCurr);
        sendBuffers();
        m_updateNeeded = false;
    }
}

void DecalGraphics::drawDot(
    uint32_t meshIndex, const pxr::GfVec3f& normal, const pxr::GfVec3f& position, float width, float offset)
{
    pxr::GfMatrix4d tm = createPointNormalTm(position + offset * normal, normal);
    tm.SetRow3(0, tm.GetRow3(0) * (0.5 * width));
    tm.SetRow3(1, tm.GetRow3(1) * (0.5 * width));
    setNextInstance(meshIndex, tm);
}

void DecalGraphics::drawLine(uint32_t meshIndex,
                             const pxr::GfVec3f& normal,
                             const pxr::GfVec3f& from,
                             const pxr::GfVec3f& to,
                             float width,
                             float offset)
{
    setNextInstance(meshIndex, calculateQuadTransform(width, to - from, normal, 0.5f * (to + from) + offset * normal));
}

void DecalGraphics::drawRtTriangle(uint32_t meshIndex,
                                   bool rightAltitude,
                                   const pxr::GfVec3f& normal,
                                   const pxr::GfVec3f& position,
                                   const pxr::GfVec3f& altitude,
                                   float width,
                                   float offset)
{
    setNextInstance(
        meshIndex, calculateQuadTransform(width, altitude, normal, position + offset * normal, rightAltitude));
}

void DecalGraphics::setNextInstance(uint32_t meshIndex, const pxr::GfMatrix4d& localTransform)
{
    setInstance(m_instIndexCurr++, meshIndex, localTransform);
    if (m_instIndexCurr >= getMaxInstanceCount())
    {
        if (m_instIndexCurr >= growInstanceBuffers())
            m_instIndexCurr = 0;
    }

    m_updateNeeded = true;
}

uint32_t DecalGraphics::growInstanceBuffers()
{
    const uint32_t oldBufferSize = getMaxInstanceCount();
    const uint32_t newBufferSize = m_bufferGrowthFn(oldBufferSize);
    if (newBufferSize > oldBufferSize)
        allocate(newBufferSize);
    return getMaxInstanceCount();
}

bool DecalGraphics::create(pxr::UsdStageWeakPtr stage, pxr::SdfPath path)
{
    // Initialize Instancer base
    Instancer::init(stage, path, m_initialBufferSize);

    pxr::UsdPrim decalPrim = getPrim();
    if (!decalPrim.IsValid())
        return false;

    m_instIndexPrev = m_instIndexCurr = 0;
    decalPrim.CreateAttribute(sCurrentInstanceIndexToken, pxr::SdfValueTypeNames->UInt).Set(m_instIndexCurr);

    m_updateNeeded = true;

    return true;
}

bool DecalGraphics::load(pxr::UsdPrim decalPrim)
{
    if (!fillFromPrim(decalPrim))
    {
        CARB_LOG_ERROR("omni::kit::decals::DecalGraphics::load: decal root prim invalid.  Cannot initialize.");
        return false;
    }

    const uint32_t maxInstanceCount = getMaxInstanceCount();

    if (getMaxInstanceCount() == 0)
    {
        CARB_LOG_ERROR(
            "omni::kit::decals::DecalGraphics::load: %s value is zero.  Cannot initialize.", "getMaxInstanceCount()");
        return false;
    }

    if (!decalPrim.GetAttribute(sCurrentInstanceIndexToken).Get(&m_instIndexCurr))
    {
        CARB_LOG_ERROR("omni::kit::decals::DecalGraphics::load: %s value not found.  Cannot initialize.",
                       sCurrentInstanceIndexToken.GetText());
        return false;
    }

    if (m_instIndexCurr >= maxInstanceCount)
    {
        CARB_LOG_WARN("omni::kit::decals::DecalGraphics::load: %s value out of range.  Setting to zero.",
                      sCurrentInstanceIndexToken.GetText());
        m_instIndexCurr = 0;
    }

    m_instIndexPrev = m_instIndexCurr;

    return true;
}


/////////////////////////////


class DrawingManager : public IDrawingManager
{
public:
    DrawingManager(pxr::UsdStageWeakPtr stage);

    virtual void updateGraphics() override;
    virtual void release() override;

    virtual void setPenColor(const Float3& rgbColor) override;
    virtual void setPenWidth(float width) override;
    virtual void setPenOffset(float offset) override;
    virtual void setPenThreshold(float threshold) override;
    virtual void setSurfacePrim(pxr::UsdPrim prim = pxr::UsdPrim()) override;
    virtual void setPen(bool down, const Float3& position, const Float3& normal) override;
    virtual bool clearSurfacePrim(pxr::UsdPrim prim) override;
    virtual void clearAllSurfacePrims() override;

private:
    enum Component
    {
        eEndcap,
        eLine,
        eTriangle,

        eComponentCount
    };

    void createMeshClasses();

    void reconstructColorMap();

    void updatePenColor();

    void drawDot(const pxr::GfVec3f& normal, const pxr::GfVec3f& position, float width, float offset)
    {
        updatePenColor();
        if (m_colorBaseIndex >= 0)
            m_graphics.drawDot(m_colorBaseIndex + eEndcap, normal, position, width, offset);
    }

    void drawLine(const pxr::GfVec3f& normal, const pxr::GfVec3f& from, const pxr::GfVec3f& to, float width, float offset)
    {
        updatePenColor();
        if (m_colorBaseIndex >= 0)
            m_graphics.drawLine(m_colorBaseIndex + eLine, normal, from, to, width, offset);
    }

    void drawRtTriangle(bool rightAltitude,
                        const pxr::GfVec3f& normal,
                        const pxr::GfVec3f& position,
                        const pxr::GfVec3f& altitude,
                        float width,
                        float offset)
    {
        updatePenColor();
        if (m_colorBaseIndex >= 0)
            m_graphics.drawRtTriangle(
                m_colorBaseIndex + eTriangle, rightAltitude, normal, position, altitude, width, offset);
    }

    void draw();

    pxr::UsdStageWeakPtr m_stage;

    // Pen parameters
    float m_penWidth;
    float m_penOffset;
    float m_penThresholdSq;
    uint32_t m_penColor;

    // Pen state
    pxr::GfVec3f m_pPrev;
    pxr::GfVec3f m_nPrev;
    pxr::GfVec3f m_pCurr;
    pxr::GfVec3f m_nCurr;
    bool m_penDown;
    uint32_t m_newPenColor;

    // Graphics management
    int m_colorBaseIndex;
    pxr::UsdPrim m_surfacePrim;
    DecalGraphics m_graphics;
    std::string m_meshClassNames[eComponentCount];

    // Serialized/reconstructed
    std::map<uint32_t, int> m_colorMap;
    pxr::SdfPathVector m_meshPaths;
};

DrawingManager::DrawingManager(pxr::UsdStageWeakPtr stage)
    : m_stage(stage),
      m_penWidth(1.0f),
      m_penOffset(0.01f),
      m_penThresholdSq(100.0f),
      m_penColor(0),
      m_pPrev(0.0f),
      m_nPrev(pxr::GfVec3f(0.0f, 0.0f, 1.0f)),
      m_pCurr(0.0f),
      m_nCurr(pxr::GfVec3f(0.0f, 0.0f, 1.0f)),
      m_penDown(false),
      m_newPenColor(0x00FFFFFF),
      m_colorBaseIndex(-1),
      m_graphics(1000, [](uint32_t s) { return s + 1000; })
{
    createMeshClasses();
}

void DrawingManager::updateGraphics()
{
    m_graphics.draw();
}

void DrawingManager::release()
{
    delete this;
}

void DrawingManager::setPenColor(const Float3& rgbColor)
{
    if (rgbColor.x < 0.0f || rgbColor.x > 1.0f || rgbColor.y < 0.0f || rgbColor.y > 1.0f || rgbColor.z < 0.0f ||
        rgbColor.z > 1.0f)
    {
        CARB_LOG_WARN("omni::kit::decals::DrawingManager::setPenColor: rgbColor component values must lie in [0.0, 1.0].");
        return;
    }

    m_newPenColor = rgbVecToVal(pxr::GfVec3f(rgbColor.x, rgbColor.y, rgbColor.z));
}

void DrawingManager::setPenWidth(float width)
{
    if (width < 0.0f)
    {
        CARB_LOG_WARN("omni::kit::decals::DrawingManager::setPenWidth: width must be non-negative.");
        return;
    }

    m_penWidth = width;
}

void DrawingManager::setPenOffset(float offset)
{
    m_penOffset = offset;
}

void DrawingManager::setPenThreshold(float threshold)
{
    if (threshold < 0.0f)
    {
        CARB_LOG_WARN("omni::kit::decals::DrawingManager::setPenThreshold: threshold must be non-negative.");
        return;
    }

    m_penThresholdSq = threshold * threshold;
}

void DrawingManager::setSurfacePrim(pxr::UsdPrim prim)
{
    if (m_surfacePrim == prim)
        return;

    updatePenColor();

    if (m_meshPaths.size() == 0)
    {
        CARB_LOG_WARN(
            "omni::kit::decals::DrawingManager::setSurfacePrim: No prototype meshes, instancer will not be initialized.");
        return;
    }

    m_surfacePrim = prim;
    if (m_graphics.isInitialized())
    {
        m_graphics.resetStroke();
        m_pPrev = m_pCurr;
        m_nPrev = m_nCurr;
    }
    reconstructColorMap();
    m_graphics.init(m_surfacePrim, m_meshPaths);
}

void DrawingManager::setPen(bool down, const Float3& position, const Float3& normal)
{
    // Update current pen values
    m_pCurr = pxr::GfVec3f(position.x, position.y, position.z);
    m_nCurr = pxr::GfVec3f(normal.x, normal.y, normal.z).GetNormalized();

    if (!m_penDown)
    {
        // If pen is up, previous values keep up with current values
        m_pPrev = m_pCurr;
        m_nPrev = m_nCurr;

        if (down)
        {
            drawDot(m_nCurr, m_pCurr, m_penWidth, m_penOffset);
            m_graphics.advanceStroke();
        }
    }
    else
    {
        // Update latest stroke
        m_graphics.resetStroke();

        if (down)
        {
            draw();

            // If distance threshold has been exceeded, start a new line
            if ((m_pCurr - m_pPrev).GetLengthSq() >= m_penThresholdSq)
            {
                m_graphics.advanceStroke();
                m_pPrev = m_pCurr;
                m_nPrev = m_nCurr;
            }
        }
    }

    m_penDown = down;
}

bool DrawingManager::clearSurfacePrim(pxr::UsdPrim prim)
{
    if (m_surfacePrim == prim)
        setSurfacePrim();

    pxr::UsdStageWeakPtr stage = prim.GetStage();
    const std::string decalPathStr = prim.GetPath().GetString() + "/" + DECAL_NAME;
    return stage->RemovePrim(pxr::SdfPath(decalPathStr));
}

void DrawingManager::clearAllSurfacePrims()
{
    static pxr::TfToken decalNameToken(DECAL_NAME);

    std::vector<pxr::SdfPath> pathsToRemove;
    for (pxr::UsdPrim prim : m_stage->Traverse())
        if (prim.IsA<pxr::UsdGeomPointInstancer>() && prim.GetName() == decalNameToken)
        {
            pathsToRemove.push_back(prim.GetPath());
            if (m_surfacePrim == prim.GetParent())
                setSurfacePrim();
        }

    for (const pxr::SdfPath& path : pathsToRemove)
        m_stage->RemovePrim(path);
}

void DrawingManager::createMeshClasses()
{
    MeshClassCreateCircle endcap;
    MeshClassCreateSquare line;
    MeshClassCreateTriangle triangle;
    MeshClassCreate* meshCreators[eComponentCount] = { &endcap, &line, &triangle };

    for (int i = 0; i < eComponentCount; ++i)
    {
        pxr::UsdGeomMesh mesh = meshCreators[i]->create(m_stage);
        m_meshClassNames[i] = meshCreators[i]->name();
    }
}

void DrawingManager::reconstructColorMap()
{
    if (!m_colorMap.empty())
        return;

    const pxr::SdfPath containerPath(DECAL_MESH_CONTAINER_PATH);

    pxr::UsdPrim containerPrim = m_stage->GetPrimAtPath(containerPath);
    containerPrim.GetRelationship(sInstancedMeshesToken).GetTargets(&m_meshPaths);

    for (size_t index = 0; index < m_meshPaths.size(); ++index)
    {
        const pxr::SdfPath& path = m_meshPaths[index];
        pxr::UsdPrim meshPrim = m_stage->GetPrimAtPath(path);
        pxr::GfVec3f color;
        pxr::UsdGeomMesh(meshPrim).GetDisplayColorAttr().Get(&color);
        const uint32_t val = rgbVecToVal(color);
        std::map<uint32_t, int>::const_iterator colorEntry = m_colorMap.find(val);
        if (colorEntry == m_colorMap.end())
            m_colorMap[val] = (int)index;
    }
}

void DrawingManager::updatePenColor()
{
    if (m_newPenColor == m_penColor)
        return;

    m_penColor = m_newPenColor;

    char colorHexStr[8];
    char* c = colorHexStr + sizeof(colorHexStr) / sizeof(char) - 1;
    uint32_t v = m_penColor;
    for (*c-- = '\0'; c > colorHexStr; v >>= 4)
        *c-- = "0123456789ABCDEF"[v & 0xF];
    *c = 'x';

    reconstructColorMap();

    std::map<uint32_t, int>::const_iterator colorEntry = m_colorMap.find(m_penColor);
    if (colorEntry != m_colorMap.end())
        m_colorBaseIndex = colorEntry->second;
    else
    {
        const size_t oldSize = m_meshPaths.size();

        // Need to create meshes for this color
        const std::string containerPath(DECAL_MESH_CONTAINER_PATH);
        const std::string colorPath = containerPath + "/" + colorHexStr;

        pxr::UsdGeomScope::Define(m_stage, pxr::SdfPath(colorPath));

        for (int i = 0; i < eComponentCount; ++i)
        {
            const pxr::SdfPath meshPath(colorPath + "/" + m_meshClassNames[i]);
            pxr::UsdGeomMesh mesh = pxr::UsdGeomMesh::Define(m_stage, meshPath);
            if (!mesh.GetPrim().IsValid())
            {
                CARB_LOG_ERROR("omni::kit::decals::DrawingManager::setPenColor: could not create meshes for color %s.\n",
                               colorHexStr);
                m_meshPaths.resize(oldSize);
                return;
            }
            m_meshPaths.push_back(meshPath);
            mesh.GetPrim().GetInherits().AddInherit(pxr::SdfPath(containerPath + "/" + m_meshClassNames[i]));
            mesh.GetDisplayColorAttr().Set(pxr::VtVec3fArray(1, rgbValToVec(m_penColor)));
        }

        m_colorMap[m_penColor] = m_colorBaseIndex = (int)oldSize;

        pxr::UsdPrim containerPrim = m_stage->GetPrimAtPath(pxr::SdfPath(containerPath));
        containerPrim.GetRelationship(sInstancedMeshesToken).SetTargets(m_meshPaths);

        if (m_graphics.isInitialized())
            m_graphics.setMeshes(m_meshPaths);
    }
}

void DrawingManager::draw()
{
    constexpr float kCosNormalTolerance = 0.99995f;

    // See how the surface normal has changed
    const float c = pxr::GfDot(m_nPrev, m_nCurr);
    if (c > -kCosNormalTolerance) // Only draw if normals are not anti-parallel (or nearly so)
    {
        if (c >= kCosNormalTolerance) // If normals are parallel (or nearly so), use a single stroke
            drawLine(m_nCurr, m_pPrev, m_pCurr, m_penWidth, m_penOffset);
        else
        { // Otherwise split stroke
            // Direction of split edge
            pxr::GfVec3f e = pxr::GfCross(m_nCurr, m_nPrev);

            // Find position on edge closest to m_pCurr, label it a0
            pxr::GfMatrix3f transposeCofM;
            transposeCofM.SetRow(0, m_nPrev - c * m_nCurr);
            transposeCofM.SetRow(1, m_nCurr - c * m_nPrev);
            transposeCofM.SetRow(2, e);
            const pxr::GfVec3f b(pxr::GfDot(m_pPrev, m_nPrev), pxr::GfDot(m_pCurr, m_nCurr), pxr::GfDot(m_pCurr, e));
            const pxr::GfVec3f a0 = (b * transposeCofM) / (1.0f - c * c);

            // Rotate m_pCurr about edge at a0, so that it's in plane 1, label result p
            const pxr::GfVec3f pPerp = m_pCurr - a0;
            const pxr::GfVec3f p = c * pPerp + pxr::GfCross(e, pPerp) + a0;

            // Intersect ray from m_nPrev in direction of p with plane 2, call it x (the position on edge to join split)
            const pxr::GfVec3f r = p - m_pPrev;
            const pxr::GfVec3f x = m_pPrev + (pxr::GfDot(m_pCurr - m_pPrev, m_nCurr) / pxr::GfDot(r, m_nCurr)) * r;

            // Use normalized e from here on
            e.Normalize();

            // First part of stroke
            pxr::GfVec3f dir1 = x - m_pPrev;
            const float l1 = dir1.Normalize();
            const float eDir1 = pxr::GfDot(dir1, e);
            const float delta1 = std::abs(eDir1 * m_penWidth) / sqrt(1.0f - eDir1 * eDir1);
            if (0.5f * delta1 < l1)
            {
                const pxr::GfVec3f altitude = delta1 * dir1;
                drawLine(m_nPrev, m_pPrev, x - 0.5f * altitude, m_penWidth, m_penOffset);
                drawRtTriangle(eDir1 > 0.0f, m_nPrev, x, altitude, m_penWidth, m_penOffset);
            }

            // Second part of stroke
            pxr::GfVec3f dir2 = x - m_pCurr;
            const float l2 = dir2.Normalize();
            const float eDir2 = pxr::GfDot(dir2, e);
            const float delta2 = std::abs(eDir2 * m_penWidth) / sqrt(1.0f - eDir2 * eDir2);
            if (0.5f * delta2 < l2)
            {
                const pxr::GfVec3f altitude = delta2 * dir2;
                drawRtTriangle(eDir2 < 0.0f, m_nCurr, x, altitude, m_penWidth, m_penOffset);
                drawLine(m_nCurr, x - 0.5f * altitude, m_pCurr, m_penWidth, m_penOffset);
            }
        }
        drawDot(m_nCurr, m_pCurr, m_penWidth, m_penOffset);
    }
}

// Global create function
IDrawingManager* createDrawingManager(pxr::UsdStageWeakPtr stage)
{
    if (stage == nullptr)
        return nullptr;

    return new DrawingManager(stage);
}

} // namespace omni
} // namespace isaac
} // namespace decals
