// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

#include <carb/logging/Log.h>

#include <isaacsim/core/experimental/prims/IPrimDataReader.h>
#include <isaacsim/core/experimental/prims/IPrimDataReaderManager.h>
#include <isaacsim/core/includes/BaseResetNode.h>
#include <isaacsim/core/includes/PhysicsEngine.h>
#include <isaacsim/core/simulation_manager/ISimulationManager.h>
#include <omni/fabric/FabricUSD.h>
#include <pxr/base/gf/vec3d.h>
#include <pxr/base/gf/vec4d.h>
#include <pxr/usd/usdGeom/camera.h>
#include <pxr/usd/usdPhysics/articulationRootAPI.h>

#include <OgnIsaacComputeTransformTreeDatabase.h>
#include <algorithm>
#include <atomic>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace isaacsim
{
namespace core
{
namespace nodes
{

using experimental::prims::IArticulationDataView;
using experimental::prims::IPrimDataReader;
using experimental::prims::IPrimDataReaderManager;
using experimental::prims::IXformDataView;

static std::atomic<int> s_transformTreeViewCounter{ 0 };

/// View index value meaning "use world or optional parent prim" (not an index into m_viewPaths).
static constexpr int kWorldParentViewIdx = -1;

/// Per-link-pair record: which view indices are the parent and child, plus cached tokens.
struct TransformPair
{
    int parentViewIdx; ///< kWorldParentViewIdx = world/external parent; >= 0 = index in m_viewPaths
    int childViewIdx; ///< index in m_viewPaths
    bool isCamera; ///< true if child is a UsdGeomCamera (needs 180° x-axis rotation for ROS convention)
    NameToken parentToken; ///< cached token (avoid per-frame stringToToken)
    NameToken childToken;
};

/// World-space position + orientation in float32, matching IPrimDataReader's float arrays directly.
struct WorldPose
{
    float px, py, pz;
    float qw, qx, qy, qz; ///< (w, x, y, z) to match Fabric decomposeMatrix layout
};

/// Hamilton product: out = a * b.
static inline void quatMul(
    float aw, float ax, float ay, float az, float bw, float bx, float by, float bz, float& ow, float& ox, float& oy, float& oz)
{
    ow = aw * bw - ax * bx - ay * by - az * bz;
    ox = aw * bx + ax * bw + ay * bz - az * by;
    oy = aw * by - ax * bz + ay * bw + az * bx;
    oz = aw * bz + ax * by - ay * bx + az * bw;
}

/// Rotate vector (vx,vy,vz) by unit quaternion (qw,qx,qy,qz) using the
/// cross-product form: result = v + 2w*(q×v) + 2*(q×(q×v)).
static inline void rotateVec(
    float qw, float qx, float qy, float qz, float vx, float vy, float vz, float& ox, float& oy, float& oz)
{
    float tx = 2.0f * (qy * vz - qz * vy);
    float ty = 2.0f * (qz * vx - qx * vz);
    float tz = 2.0f * (qx * vy - qy * vx);
    ox = vx + qw * tx + (qy * tz - qz * ty);
    oy = vy + qw * ty + (qz * tx - qx * tz);
    oz = vz + qw * tz + (qx * ty - qy * tx);
}

class OgnIsaacComputeTransformTree : public isaacsim::core::includes::BaseResetNode
{
public:
    ~OgnIsaacComputeTransformTree()
    {
        cleanupView();
    }

    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnIsaacComputeTransformTreeDatabase::sPerInstanceState<OgnIsaacComputeTransformTree>(nodeObj, instanceId);
        state.m_simManager = carb::getCachedInterface<isaacsim::core::simulation_manager::ISimulationManager>();
        state.m_readerManager = carb::getCachedInterface<IPrimDataReaderManager>();
    }

    static bool compute(OgnIsaacComputeTransformTreeDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();
        auto& state = db.perInstanceState<OgnIsaacComputeTransformTree>();

        if (!state.ensureCurrentView(db, context))
        {
            return false;
        }

        if (!state.m_xformView)
        {
            return false;
        }

        return state.computeTransforms(db);
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnIsaacComputeTransformTreeDatabase::sPerInstanceState<OgnIsaacComputeTransformTree>(nodeObj, instanceId);
        state.reset();
    }

    void reset() override
    {
        cleanupView();
        m_firstFrame = true;
        m_viewPaths.clear();
        m_cameraViewIndices.clear();
        m_pairs.clear();
        m_parentPoseCache.clear();
        m_parentPoseCacheValid.clear();
        m_lastNumPairs = -1;
        m_parentPath.clear();
        m_parentFrame = "world";
        m_frameNamesStale = true;
    }

private:
    bool ensureCurrentView(OgnIsaacComputeTransformTreeDatabase& db, const GraphContextObj& context)
    {
        if (!m_simManager || !m_simManager->isSimulating())
        {
            return false;
        }

        if (m_firstFrame)
        {
            return initialize(db, context);
        }

        if (m_reader && m_reader->getGeneration() != m_readerGeneration)
        {
            reset();
            return initialize(db, context);
        }

        return m_xformView != nullptr;
    }

    bool initialize(OgnIsaacComputeTransformTreeDatabase& db, const GraphContextObj& context)
    {
        long stageId = context.iContext->getStageId(context);

        if (!createXformViewSetup(db, stageId))
        {
            return false;
        }

        std::unordered_map<std::string, std::string> linkParents;
        if (!collectViewPathsAndLinkParents(db, linkParents, stageId))
        {
            return false;
        }

        if (!createXformView(db, stageId))
        {
            return false;
        }

        if (!resolveParentPrim(db))
        {
            return false;
        }

        buildTransformPairs(linkParents);

        m_firstFrame = false;
        m_frameNamesStale = true;
        return true;
    }

    /// Setup the reader/manager before resolving paths (called first in initialize()).
    bool createXformViewSetup(OgnIsaacComputeTransformTreeDatabase& db, long stageId)
    {
        if (!m_readerManager)
        {
            db.logError("Failed to acquire IPrimDataReaderManager interface");
            return false;
        }
        if (!m_readerManager->ensureInitialized(stageId, -1))
        {
            db.logError("Failed to initialize shared prim data reader session");
            return false;
        }
        m_reader = m_readerManager->getReader();
        if (!m_reader)
        {
            db.logError("Failed to acquire shared IPrimDataReader interface");
            return false;
        }
        m_readerGeneration = m_reader->getGeneration();
        return true;
    }

    /// Resolves parent prim from input; matches OgnROS2PublishTransformTree (legacy): no validation, path used as-is.
    /// Must be called after createXformView() so m_xformView is available.
    bool resolveParentPrim(OgnIsaacComputeTransformTreeDatabase& db)
    {
        const auto& parentPrimInput = db.inputs.parentPrim();
        if (parentPrimInput.empty())
        {
            return true;
        }
        m_parentPath = omni::fabric::toSdfPath(parentPrimInput[0]).GetString();
        char nameBuf[256] = {};
        if (m_xformView->getPrimFrameName(m_parentPath.c_str(), nameBuf, sizeof(nameBuf)))
        {
            m_parentFrame = nameBuf;
        }
        return true;
    }

    bool collectViewPathsAndLinkParents(OgnIsaacComputeTransformTreeDatabase& db,
                                        std::unordered_map<std::string, std::string>& linkParents,
                                        long stageId)
    {
        const auto& targetPrims = db.inputs.targetPrims();
        if (targetPrims.empty())
        {
            db.logError("Please specify at least one valid target prim");
            return false;
        }

        // Obtain the stage to guard articulation discovery with a cheap API check, avoiding
        // spurious PhysX tensor errors for sensor/camera/Xform-only prims.
        pxr::UsdStageRefPtr stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
        if (!stage)
        {
            db.logError("Could not find USD stage %ld", stageId);
            return false;
        }

        for (size_t i = 0; i < targetPrims.size(); i++)
        {
            std::string primPathStr = omni::fabric::toSdfPath(targetPrims[i]).GetString();

            // Guard against empty or non-absolute paths from disconnected/deleted target prim definitions.
            if (primPathStr.empty() || primPathStr[0] != '/')
            {
                CARB_LOG_WARN("IsaacComputeTransformTree: skipping target prim at index %zu with invalid path '%s'", i,
                              primPathStr.c_str());
                continue;
            }

            // Look up prim once for both articulation check and camera detection below.
            pxr::UsdPrim prim = stage->GetPrimAtPath(pxr::SdfPath(primPathStr));
            if (!prim)
            {
                CARB_LOG_WARN("IsaacComputeTransformTree: prim '%s' not found on stage, skipping", primPathStr.c_str());
                continue;
            }

            // Only attempt articulation discovery for prims that have UsdPhysicsArticulationRootAPI.
            // Without this guard, createArticulationView triggers PhysX tensor errors for every
            // non-physics prim (sensors, cameras, IMUs, etc.).
            bool hasArticulationApi = prim.HasAPI<pxr::UsdPhysicsArticulationRootAPI>();

            bool isArticulation = false;
            if (hasArticulationApi)
            {
                // Create a temporary articulation view to detect links via USD traversal.
                // Use "newton" engine type to avoid triggering PhysX tensor setup — getArticulationLinks
                // is pure USD traversal and does not require any physics backend to be active.
                std::string tempId = "ctt_discover_" + std::to_string(i);
                const char* pathPtr = primPathStr.c_str();
                IArticulationDataView* artView = m_reader->createArticulationView(tempId.c_str(), &pathPtr, 1, "newton");

                const experimental::prims::LinkInfo* links = nullptr;
                size_t linkCount = 0;
                isArticulation =
                    artView && artView->getArticulationLinks(primPathStr.c_str(), &links, &linkCount) && linkCount > 0;

                if (isArticulation)
                {
                    // Copy link data before removing the view (pointers become invalid after removeView).
                    std::vector<std::pair<std::string, std::string>> copied(linkCount);
                    for (size_t j = 0; j < linkCount; j++)
                        copied[j] = { links[j].path, links[j].parentPath };
                    m_reader->removeView(tempId.c_str());
                    for (const auto& [path, parentPath] : copied)
                    {
                        m_viewPaths.push_back(path);
                        linkParents[path] = parentPath;
                    }
                }
                else
                {
                    m_reader->removeView(tempId.c_str());
                }
            }

            if (!isArticulation)
            {
                // Not an articulation (or no links found): treat as a single prim.
                int viewIdx = static_cast<int>(m_viewPaths.size());
                m_viewPaths.push_back(primPathStr);
                linkParents[primPathStr] = "";

                // Cameras need a 180° x-axis rotation to match the ROS optical frame convention.
                if (prim.IsA<pxr::UsdGeomCamera>())
                    m_cameraViewIndices.insert(viewIdx);
            }
        }

        if (m_viewPaths.empty())
        {
            db.logError("No valid prims found after resolving target prims");
            return false;
        }
        return true;
    }

    bool createXformView(OgnIsaacComputeTransformTreeDatabase& db, long /*stageId*/)
    {
        m_viewId = "compute_transform_tree_" + std::to_string(s_transformTreeViewCounter.fetch_add(1));
        std::vector<const char*> pathPtrs;
        pathPtrs.reserve(m_viewPaths.size());
        for (const auto& p : m_viewPaths)
        {
            pathPtrs.push_back(p.c_str());
        }
        const char* engine = isaacsim::core::includes::getActivePhysicsEngineName();
        m_xformView = m_reader->createXformView(m_viewId.c_str(), pathPtrs.data(), pathPtrs.size(), engine);
        if (!m_xformView)
        {
            db.logError("Failed to create xform view");
            return false;
        }
        return true;
    }

    // Records only pair topology (indices + isCamera). Frame names and tokens are filled by rebuildFrameNames().
    void buildTransformPairs(const std::unordered_map<std::string, std::string>& linkParents)
    {
        std::unordered_map<std::string, int> pathIndex;
        for (size_t i = 0; i < m_viewPaths.size(); i++)
            pathIndex[m_viewPaths[i]] = static_cast<int>(i);

        for (size_t i = 0; i < m_viewPaths.size(); i++)
        {
            const std::string& childPath = m_viewPaths[i];
            const auto& parentPath = linkParents.at(childPath);
            bool isCamera = m_cameraViewIndices.count(static_cast<int>(i)) > 0;

            if (parentPath.empty())
            {
                m_pairs.push_back({ kWorldParentViewIdx, static_cast<int>(i), isCamera });
            }
            else
            {
                auto it = pathIndex.find(parentPath);
                m_pairs.push_back(
                    { it != pathIndex.end() ? it->second : kWorldParentViewIdx, static_cast<int>(i), isCamera });
            }
        }

        m_parentPoseCache.resize(m_viewPaths.size());
        m_parentPoseCacheValid.resize(m_viewPaths.size(), 0);
    }

    /// Re-reads all frame names from the xform view (after nameOverrides are fully authored) and
    /// updates m_pairs tokens. Called on the first compute frame after initialize().
    /// Each node instance resolves names independently, so multiple robots can
    /// each own frame names like 'front_fisheye_camera' without cross-node interference.
    void rebuildFrameNames(OgnIsaacComputeTransformTreeDatabase& db)
    {
        if (!m_parentPath.empty())
        {
            char nameBuf[256] = {};
            if (m_xformView->getPrimFrameName(m_parentPath.c_str(), nameBuf, sizeof(nameBuf)))
                m_parentFrame = nameBuf;
        }

        const size_t n = m_viewPaths.size();

        // Collect desired frame name for every prim (nameOverride or USD leaf name as fallback).
        std::vector<std::string> desired(n);
        for (size_t i = 0; i < n; ++i)
        {
            char nameBuf[256] = {};
            if (m_xformView->getPrimFrameName(m_viewPaths[i].c_str(), nameBuf, sizeof(nameBuf)))
                desired[i] = nameBuf;
            else
            {
                auto slash = m_viewPaths[i].rfind('/');
                desired[i] = (slash != std::string::npos) ? m_viewPaths[i].substr(slash + 1) : m_viewPaths[i];
            }
        }

        // Deepest-path preference: for each desired name, record the prim with the longest path
        // (sensor leaves take priority over mount parents with the same nameOverride).
        std::unordered_map<std::string, size_t> deepest;
        for (size_t i = 0; i < n; ++i)
        {
            auto [it, inserted] = deepest.emplace(desired[i], i);
            if (!inserted && m_viewPaths[i].size() > m_viewPaths[it->second].size())
                it->second = i;
        }

        std::vector<std::string> frameNames(n);

        // Primaries get their desired name directly.
        for (size_t i = 0; i < n; ++i)
        {
            if (deepest.at(desired[i]) == i)
                frameNames[i] = desired[i];
        }

        // Non-primaries (e.g. mount prims that lost leaf-preference) fall back to USD leaf name.
        // If that is also taken (two prims share a USD leaf name), walk ancestors for a qualified name.
        const size_t startPos = firstComponentEnd();
        std::unordered_map<std::string, std::string> nameCache;
        for (size_t i = 0; i < n; ++i)
        {
            if (!frameNames[i].empty())
                continue;

            const std::string& path = m_viewPaths[i];
            auto slash = path.rfind('/');
            std::string leafName = (slash != std::string::npos) ? path.substr(slash + 1) : path;

            std::string name = std::find(frameNames.begin(), frameNames.end(), leafName) != frameNames.end() ?
                                   disambiguateFrameName(path, leafName, startPos, frameNames, nameCache) :
                                   leafName;

            if (desired[i] != name)
                CARB_LOG_WARN(
                    "Frame '%s' already exists (used by another prim). Using '%s' for '%s'. "
                    "Set unique `isaac:nameOverride` values per robot instance to suppress this.",
                    desired[i].c_str(), name.c_str(), path.c_str());

            frameNames[i] = name;
        }

        for (auto& pair : m_pairs)
        {
            pair.childToken = db.stringToToken(frameNames[pair.childViewIdx].c_str());
            const std::string& parentName =
                (pair.parentViewIdx != kWorldParentViewIdx) ? frameNames[pair.parentViewIdx] : m_parentFrame;
            pair.parentToken = db.stringToToken(parentName.c_str());
        }

        m_frameNamesStale = false;
    }

    bool computeTransforms(OgnIsaacComputeTransformTreeDatabase& db)
    {
        if (m_frameNamesStale)
            rebuildFrameNames(db);

        const auto poses = m_xformView->getWorldPosesHost();
        const float* positions = poses.positions;
        const float* orientations = poses.orientations;

        const size_t numViews = m_viewPaths.size();
        if (!positions || !orientations || static_cast<size_t>(poses.posCount) < numViews * 3 ||
            static_cast<size_t>(poses.oriCount) < numViews * 4)
        {
            return false;
        }

        WorldPose parentWorldPose{ 0, 0, 0, 1, 0, 0, 0 };
        if (!m_parentPath.empty())
        {
            float pos[3] = {}, ori[4] = {};
            if (m_xformView->getPrimWorldTransform(m_parentPath.c_str(), pos, ori))
            {
                parentWorldPose = { pos[0], pos[1], pos[2], ori[0], ori[1], ori[2], ori[3] };
            }
        }

        const int numPairs = static_cast<int>(m_pairs.size());

        auto& outParentFrames = db.outputs.parentFrames();
        auto& outChildFrames = db.outputs.childFrames();
        auto& outTranslations = db.outputs.translations();
        auto& outOrientations = db.outputs.orientations();

        if (numPairs != m_lastNumPairs)
        {
            outParentFrames.resize(numPairs);
            outChildFrames.resize(numPairs);
            outTranslations.resize(numPairs);
            outOrientations.resize(numPairs);
            m_lastNumPairs = numPairs;
        }

        std::fill(m_parentPoseCacheValid.begin(), m_parentPoseCacheValid.end(), static_cast<uint8_t>(0));

        for (int i = 0; i < numPairs; i++)
        {
            const auto& pair = m_pairs[i];

            WorldPose childPose = worldPoseFromView(positions, orientations, pair.childViewIdx);

            if (pair.isCamera)
            {
                float cw, cx, cy, cz;
                quatMul(childPose.qw, childPose.qx, childPose.qy, childPose.qz, 0.0f, 1.0f, 0.0f, 0.0f, cw, cx, cy, cz);
                childPose.qw = cw;
                childPose.qx = cx;
                childPose.qy = cy;
                childPose.qz = cz;
            }

            const WorldPose* refPose = nullptr;
            if (pair.parentViewIdx == kWorldParentViewIdx)
            {
                refPose = &parentWorldPose;
            }
            else
            {
                int idx = pair.parentViewIdx;
                if (!m_parentPoseCacheValid[idx])
                {
                    m_parentPoseCache[idx] = worldPoseFromView(positions, orientations, idx);
                    m_parentPoseCacheValid[idx] = 1;
                }
                refPose = &m_parentPoseCache[idx];
            }

            float relTx, relTy, relTz, relQw, relQx, relQy, relQz;
            computeRelativeTransform(*refPose, childPose, relTx, relTy, relTz, relQw, relQx, relQy, relQz);

            outParentFrames[i] = pair.parentToken;
            outChildFrames[i] = pair.childToken;
            outTranslations[i] = pxr::GfVec3d(relTx, relTy, relTz);
            outOrientations[i] = pxr::GfVec4d(relQx, relQy, relQz, relQw);
        }

        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

    /// Read a WorldPose directly from the float arrays with zero conversion.
    static WorldPose worldPoseFromView(const float* positions, const float* orientations, int idx)
    {
        return { positions[3 * idx],        positions[3 * idx + 1],    positions[3 * idx + 2],   orientations[4 * idx],
                 orientations[4 * idx + 1], orientations[4 * idx + 2], orientations[4 * idx + 3] };
    }

    /// Compute child-in-parent relative transform using inline float32 quaternion math.
    static void computeRelativeTransform(const WorldPose& parent,
                                         const WorldPose& child,
                                         float& outTx,
                                         float& outTy,
                                         float& outTz,
                                         float& outQw,
                                         float& outQx,
                                         float& outQy,
                                         float& outQz)
    {
        float piw = parent.qw, pix = -parent.qx, piy = -parent.qy, piz = -parent.qz;
        quatMul(piw, pix, piy, piz, child.qw, child.qx, child.qy, child.qz, outQw, outQx, outQy, outQz);
        rotateVec(
            piw, pix, piy, piz, child.px - parent.px, child.py - parent.py, child.pz - parent.pz, outTx, outTy, outTz);
    }

    /// Returns the byte offset of the slash that ends the first path component (e.g. 6 for
    /// "/World/..."). Used by disambiguateFrameName so the first ancestor qualifier tried is the
    /// robot-level prim (e.g. /World/Nova_Carter_ROS_1), which is unique per robot instance.
    size_t firstComponentEnd() const
    {
        if (m_viewPaths.empty())
            return 0;
        size_t pos = m_viewPaths[0].find('/', 1);
        return (pos != std::string::npos) ? pos : 0;
    }

    /// Builds a qualified frame name by prepending ancestor path components to @p leaf, starting
    /// past the first path component (e.g. past /World). Returns the first unused candidate,
    /// or a path slug from @p startPos as a last resort.
    std::string disambiguateFrameName(const std::string& path,
                                      const std::string& leaf,
                                      size_t startPos,
                                      const std::vector<std::string>& frameNames,
                                      std::unordered_map<std::string, std::string>& nameCache)
    {
        auto taken = [&](const std::string& s)
        { return std::find(frameNames.begin(), frameNames.end(), s) != frameNames.end(); };
        if (path.size() > 1 && path[0] == '/')
        {
            size_t pos = startPos;
            while (true)
            {
                size_t nextSlash = path.find('/', pos + 1);
                if (nextSlash == std::string::npos)
                    break;
                std::string ancestorPath = path.substr(0, nextSlash);
                auto it = nameCache.find(ancestorPath);
                std::string ancestorName;
                if (it != nameCache.end())
                    ancestorName = it->second;
                else
                {
                    char nameBuf[256] = {};
                    ancestorName =
                        (m_xformView && m_xformView->getPrimFrameName(ancestorPath.c_str(), nameBuf, sizeof(nameBuf))) ?
                            nameBuf :
                            path.substr(pos + 1, nextSlash - pos - 1);
                    nameCache[ancestorPath] = ancestorName;
                }
                if (!ancestorName.empty() && ancestorName != leaf)
                {
                    std::string candidate = ancestorName + "_" + leaf;
                    if (!taken(candidate))
                        return candidate;
                }
                pos = nextSlash;
            }
        }
        // Last resort: slug the path from startPos onward, skipping the root component.
        size_t slugStart = (startPos < path.size() && path[startPos] == '/') ? startPos + 1 : startPos;
        std::string name = path.substr(slugStart);
        std::replace(name.begin(), name.end(), '/', '_');
        return name;
    }

    void cleanupView()
    {
        if (m_reader && !m_viewId.empty())
        {
            m_reader->removeView(m_viewId.c_str());
        }
        m_xformView = nullptr;
        m_reader = nullptr;
        m_readerGeneration = 0;
        m_viewId.clear();
    }

    // Interfaces
    IPrimDataReaderManager* m_readerManager = nullptr;
    IPrimDataReader* m_reader = nullptr;
    IXformDataView* m_xformView = nullptr;
    isaacsim::core::simulation_manager::ISimulationManager* m_simManager = nullptr;
    uint64_t m_readerGeneration = 0;

    // View state
    std::string m_viewId;
    std::vector<std::string> m_viewPaths; ///< All prim paths in the IXformDataView, in order
    std::unordered_set<int> m_cameraViewIndices; ///< View indices that are camera prims needing rotation
    std::vector<TransformPair> m_pairs; ///< Output parent-child pairs
    std::vector<WorldPose> m_parentPoseCache; ///< Flat cache indexed by viewIdx, avoids per-frame heap alloc
    std::vector<uint8_t> m_parentPoseCacheValid; ///< 1 = entry populated this frame

    // Parent frame
    std::string m_parentPath;
    std::string m_parentFrame = "world";

    bool m_firstFrame = true;
    bool m_frameNamesStale = true;
    int m_lastNumPairs = -1;
};

REGISTER_OGN_NODE()
} // namespace nodes
} // namespace core
} // namespace isaacsim
