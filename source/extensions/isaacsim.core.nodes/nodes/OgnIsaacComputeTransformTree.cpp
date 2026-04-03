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
#include <isaacsim/core/simulation_manager/ISimulationManager.h>
#include <omni/fabric/FabricUSD.h>
#include <pxr/base/gf/vec3d.h>
#include <pxr/base/gf/vec4d.h>
#include <pxr/base/tf/type.h>
#include <pxr/usd/usdGeom/camera.h>
#include <pxr/usd/usdPhysics/articulationRootAPI.h>

#include <OgnIsaacComputeTransformTreeDatabase.h>
#include <algorithm>
#include <atomic>
#include <map>
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

/// Per-link-pair record: which view indices are the parent and child, plus frame names and cached tokens.
struct TransformPair
{
    int parentViewIdx; ///< kWorldParentViewIdx = world/external parent; >= 0 = index in m_viewPaths
    int childViewIdx; ///< index in m_viewPaths
    std::string parentFrame;
    std::string childFrame;
    bool isCamera; ///< true if child is a UsdGeomCamera (needs 180° x-axis rotation for ROS convention)
    NameToken parentToken; ///< cached token for parentFrame (avoid per-frame stringToToken)
    NameToken childToken; ///< cached token for childFrame
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

        if (state.m_firstFrame)
        {
            if (!state.m_simManager || !state.m_simManager->isSimulating())
            {
                return false;
            }

            if (!state.initialize(db, context))
            {
                return false;
            }
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
        m_renamedFrames.clear();
        m_publishedFrames.clear();
        m_parentPath.clear();
        m_parentFrame = "world";
    }

private:
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

        buildTransformPairs(db, linkParents);

        m_firstFrame = false;
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

        for (size_t i = 0; i < targetPrims.size(); i++)
        {
            std::string primPathStr = omni::fabric::toSdfPath(targetPrims[i]).GetString();

            // Only attempt articulation discovery for prims that have UsdPhysicsArticulationRootAPI.
            // Without this guard, createArticulationView triggers PhysX tensor errors for every
            // non-physics prim (sensors, cameras, IMUs, etc.).
            bool hasArticulationApi = false;
            if (stage)
            {
                pxr::UsdPrim prim = stage->GetPrimAtPath(pxr::SdfPath(primPathStr));
                hasArticulationApi = prim && prim.HasAPI<pxr::UsdPhysicsArticulationRootAPI>();
            }

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
                    struct LinkCopy
                    {
                        std::string path;
                        std::string parentPath;
                    };
                    std::vector<LinkCopy> copied(linkCount);
                    for (size_t j = 0; j < linkCount; j++)
                    {
                        copied[j].path = links[j].path;
                        copied[j].parentPath = links[j].parentPath;
                    }
                    m_reader->removeView(tempId.c_str());
                    for (const auto& lc : copied)
                    {
                        m_viewPaths.push_back(lc.path);
                        linkParents[lc.path] = lc.parentPath;
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

                // Cameras (excluding RTX Lidar sensors that share the Camera schema) need a
                // 180° x-axis rotation to match the ROS optical frame convention.
                if (stage)
                {
                    pxr::UsdPrim prim = stage->GetPrimAtPath(pxr::SdfPath(primPathStr));
                    if (prim && prim.IsA<pxr::UsdGeomCamera>())
                    {
                        static const pxr::TfType kRtxLidarType =
                            pxr::TfType::FindByName("IsaacSensorIsaacRtxLidarSensorAPI");
                        if (!kRtxLidarType || !prim.HasAPI(kRtxLidarType))
                        {
                            m_cameraViewIndices.insert(viewIdx);
                        }
                    }
                }
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
        m_xformView = m_reader->createXformView(m_viewId.c_str(), pathPtrs.data(), pathPtrs.size(), "physx");
        if (!m_xformView)
        {
            db.logError("Failed to create xform view");
            return false;
        }
        return true;
    }

    void buildTransformPairs(OgnIsaacComputeTransformTreeDatabase& db,
                             const std::unordered_map<std::string, std::string>& linkParents)
    {
        std::unordered_map<std::string, int> pathIndex;
        for (size_t i = 0; i < m_viewPaths.size(); i++)
        {
            pathIndex[m_viewPaths[i]] = static_cast<int>(i);
        }

        std::unordered_map<std::string, std::string> pathToFrame;
        for (const auto& path : m_viewPaths)
        {
            char nameBuf[256] = {};
            std::string name;
            if (m_xformView->getPrimFrameName(path.c_str(), nameBuf, sizeof(nameBuf)))
            {
                name = nameBuf;
            }
            else
            {
                auto slash = path.rfind('/');
                name = (slash != std::string::npos) ? path.substr(slash + 1) : path;
            }
            pathToFrame[path] = getUniqueFrameName(name, path);
        }

        for (size_t i = 0; i < m_viewPaths.size(); i++)
        {
            const std::string& childPath = m_viewPaths[i];
            const std::string& childFrame = pathToFrame[childPath];
            const auto& parentPathStr = linkParents.at(childPath);
            bool isCamera = m_cameraViewIndices.count(static_cast<int>(i)) > 0;

            if (parentPathStr.empty())
            {
                m_pairs.push_back({ kWorldParentViewIdx, static_cast<int>(i), m_parentFrame, childFrame, isCamera });
            }
            else
            {
                auto it = pathIndex.find(parentPathStr);
                if (it != pathIndex.end())
                {
                    const std::string& parentFrame = pathToFrame.at(parentPathStr);
                    m_pairs.push_back({ it->second, static_cast<int>(i), parentFrame, childFrame, isCamera });
                }
                else
                {
                    m_pairs.push_back({ kWorldParentViewIdx, static_cast<int>(i), m_parentFrame, childFrame, isCamera });
                }
            }
        }

        // Cache OmniGraph tokens once — avoids per-frame stringToToken calls.
        for (auto& pair : m_pairs)
        {
            pair.parentToken = db.stringToToken(pair.parentFrame.c_str());
            pair.childToken = db.stringToToken(pair.childFrame.c_str());
        }

        m_parentPoseCache.resize(m_viewPaths.size());
        m_parentPoseCacheValid.resize(m_viewPaths.size(), 0);
    }

    bool computeTransforms(OgnIsaacComputeTransformTreeDatabase& db)
    {
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

        outParentFrames.resize(numPairs);
        outChildFrames.resize(numPairs);
        outTranslations.resize(numPairs);
        outOrientations.resize(numPairs);

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

    /// Returns a unique frame name: uses existing rename, or frame if first use, or path-derived name on collision.
    std::string getUniqueFrameName(const std::string& frame, const std::string& path)
    {
        std::string name(frame);
        auto renameIt = m_renamedFrames.find(path);
        if (renameIt != m_renamedFrames.end())
        {
            m_publishedFrames[frame] = true;
            return renameIt->second;
        }
        if (m_publishedFrames.find(frame) == m_publishedFrames.end())
        {
            m_renamedFrames[path] = frame;
            m_publishedFrames[frame] = true;
        }
        else
        {
            name = path;
            std::replace(name.begin(), name.end(), '/', '_');
            if (!name.empty() && name[0] == '_')
            {
                name = name.substr(1);
            }
            CARB_LOG_WARN(
                "Frame with name %s already exists. Overriding frame name for %s to %s "
                "(add isaac:nameOverride attribute to remove this warning)",
                frame.c_str(), path.c_str(), name.c_str());
            m_renamedFrames[path] = name;
            m_publishedFrames[name] = true;
        }
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
        m_viewId.clear();
    }

    // Interfaces
    IPrimDataReaderManager* m_readerManager = nullptr;
    IPrimDataReader* m_reader = nullptr;
    IXformDataView* m_xformView = nullptr;
    isaacsim::core::simulation_manager::ISimulationManager* m_simManager = nullptr;

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

    // Frame name deduplication
    std::map<std::string, std::string> m_renamedFrames;
    std::map<std::string, bool> m_publishedFrames;

    bool m_firstFrame = true;
};

REGISTER_OGN_NODE()
} // namespace nodes
} // namespace core
} // namespace isaacsim
