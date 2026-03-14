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
#include <pxr/base/gf/matrix4d.h>
#include <pxr/base/gf/quatd.h>
#include <pxr/base/gf/rotation.h>
#include <pxr/base/gf/vec3d.h>
#include <pxr/base/gf/vec4d.h>

#include <OgnIsaacComputeTransformTreeDatabase.h>
#include <algorithm>
#include <atomic>
#include <map>
#include <string>
#include <unordered_map>
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

/// Per-link-pair record: which view indices are the parent and child, plus frame names.
struct TransformPair
{
    int parentViewIdx; ///< kWorldParentViewIdx = world/external parent; >= 0 = index in m_viewPaths
    int childViewIdx; ///< index in m_viewPaths
    std::string parentFrame;
    std::string childFrame;
};

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
        m_pairs.clear();
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
        if (!collectViewPathsAndLinkParents(db, linkParents))
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
                                        std::unordered_map<std::string, std::string>& linkParents)
    {
        const auto& targetPrims = db.inputs.targetPrims();
        if (targetPrims.empty())
        {
            db.logError("Please specify at least one valid target prim");
            return false;
        }

        for (size_t i = 0; i < targetPrims.size(); i++)
        {
            std::string primPathStr = omni::fabric::toSdfPath(targetPrims[i]).GetString();

            // Create a temporary articulation view to detect links via USD traversal.
            std::string tempId = "ctt_discover_" + std::to_string(i);
            const char* pathPtr = primPathStr.c_str();
            IArticulationDataView* artView = m_reader->createArticulationView(tempId.c_str(), &pathPtr, 1, "physx");

            const experimental::prims::LinkInfo* links = nullptr;
            size_t linkCount = 0;
            bool isArticulation =
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
                // Not an articulation (or no links found): treat as a single prim.
                m_viewPaths.push_back(primPathStr);
                linkParents[primPathStr] = "";
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

    void buildTransformPairs(const std::unordered_map<std::string, std::string>& linkParents)
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
                // Fallback: use the last component of the path
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

            if (parentPathStr.empty())
            {
                m_pairs.push_back({ kWorldParentViewIdx, static_cast<int>(i), m_parentFrame, childFrame });
            }
            else
            {
                auto it = pathIndex.find(parentPathStr);
                if (it != pathIndex.end())
                {
                    const std::string& parentFrame = pathToFrame.at(parentPathStr);
                    m_pairs.push_back({ it->second, static_cast<int>(i), parentFrame, childFrame });
                }
                else
                {
                    // Parent link not in view (shouldn't happen); use world as parent
                    m_pairs.push_back({ kWorldParentViewIdx, static_cast<int>(i), m_parentFrame, childFrame });
                }
            }
        }
    }

    bool computeTransforms(OgnIsaacComputeTransformTreeDatabase& db)
    {
        int posCount = 0, oriCount = 0;
        const float* positions = m_xformView->getWorldPositionsHost(&posCount);
        const float* orientations = m_xformView->getWorldOrientationsHost(&oriCount);

        const size_t numViews = m_viewPaths.size();
        if (!positions || !orientations || static_cast<size_t>(posCount) < numViews * 3 ||
            static_cast<size_t>(oriCount) < numViews * 4)
        {
            return false;
        }

        // Compute parent frame world transform (identity if no parent prim)
        pxr::GfMatrix4d parentWorld(1.0);
        if (!m_parentPath.empty())
        {
            float pos[3] = {}, ori[4] = {};
            if (m_xformView->getPrimWorldTransform(m_parentPath.c_str(), pos, ori))
            {
                // ori layout: (qw, qx, qy, qz) from decomposeMatrix
                double qw = static_cast<double>(ori[0]);
                double qx = static_cast<double>(ori[1]);
                double qy = static_cast<double>(ori[2]);
                double qz = static_cast<double>(ori[3]);
                pxr::GfQuatd q(qw, qx, qy, qz);
                pxr::GfRotation rot(q);
                double px = static_cast<double>(pos[0]);
                double py = static_cast<double>(pos[1]);
                double pz = static_cast<double>(pos[2]);
                parentWorld.SetTransform(rot, pxr::GfVec3d(px, py, pz));
            }
        }
        pxr::GfMatrix4d parentWorldInv = parentWorld.GetInverse();

        const int numPairs = static_cast<int>(m_pairs.size());

        auto& outParentFrames = db.outputs.parentFrames();
        auto& outChildFrames = db.outputs.childFrames();
        auto& outTranslations = db.outputs.translations();
        auto& outOrientations = db.outputs.orientations();

        outParentFrames.resize(numPairs);
        outChildFrames.resize(numPairs);
        outTranslations.resize(numPairs);
        outOrientations.resize(numPairs);

        for (int i = 0; i < numPairs; i++)
        {
            const auto& pair = m_pairs[i];
            const int childViewIdx = pair.childViewIdx;
            const int parentViewIdx = pair.parentViewIdx;

            pxr::GfMatrix4d childWorld = worldTransformFromView(positions, orientations, childViewIdx);

            pxr::GfMatrix4d refWorldInv;
            if (parentViewIdx == kWorldParentViewIdx)
            {
                refWorldInv = parentWorldInv;
            }
            else
            {
                pxr::GfMatrix4d parentLinkWorld = worldTransformFromView(positions, orientations, parentViewIdx);
                refWorldInv = parentLinkWorld.GetInverse();
            }

            // Relative transform: childWorld * refWorldInv (row-vector convention)
            pxr::GfMatrix4d rel = childWorld * refWorldInv;

            pxr::GfVec3d relTrans = rel.ExtractTranslation();
            pxr::GfRotation relRot = rel.ExtractRotationMatrix().ExtractRotation();
            pxr::GfQuatd relQuat = relRot.GetQuat();
            pxr::GfVec3d quatImag = relQuat.GetImaginary();
            double quatReal = relQuat.GetReal();

            outParentFrames[i] = db.stringToToken(pair.parentFrame.c_str());
            outChildFrames[i] = db.stringToToken(pair.childFrame.c_str());
            outTranslations[i] = pxr::GfVec3d(relTrans[0], relTrans[1], relTrans[2]);
            outOrientations[i] = pxr::GfVec4d(quatImag[0], quatImag[1], quatImag[2], quatReal);
        }

        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

    /// Build a GfMatrix4d from the IXformDataView host float arrays for prim at index idx.
    /// Positions layout: [3*idx + 0..2] = (x, y, z)
    /// Orientations layout: [4*idx + 0..3] = (qw, qx, qy, qz) — Fabric decomposeMatrix layout
    static pxr::GfMatrix4d worldTransformFromView(const float* positions, const float* orientations, int idx)
    {
        double px = static_cast<double>(positions[3 * idx + 0]);
        double py = static_cast<double>(positions[3 * idx + 1]);
        double pz = static_cast<double>(positions[3 * idx + 2]);
        double qw = static_cast<double>(orientations[4 * idx + 0]);
        double qx = static_cast<double>(orientations[4 * idx + 1]);
        double qy = static_cast<double>(orientations[4 * idx + 2]);
        double qz = static_cast<double>(orientations[4 * idx + 3]);

        pxr::GfQuatd q(qw, qx, qy, qz);
        pxr::GfRotation rot(q);
        pxr::GfMatrix4d m;
        m.SetTransform(rot, pxr::GfVec3d(px, py, pz));
        return m;
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
    std::vector<TransformPair> m_pairs; ///< Output parent-child pairs

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
