// Copyright (c) 2024-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
// #include <omni/usd/UsdContextIncludes.h>
// #include <omni/usd/UsdContext.h>
// #include <omni/usd/UsdUtils.h>
// clang-format off
#include <pch/UsdPCH.h>
// clang-format on
#include <physxSchema/physxSceneAPI.h>
#include <pxr/base/tf/notice.h>
#include <pxr/pxr.h>

#include <functional>
#include <vector>

namespace isaacsim
{
namespace core
{
namespace simulation_manager
{

/**
 * @class UsdNoticeListener
 * @brief Listener class for USD object change notifications.
 * @details
 * This class listens for changes to USD objects and manages callbacks for deletion
 * and physics scene addition events. It inherits from pxr::TfWeakBase to support
 * the USD notification system.
 */
class UsdNoticeListener : public pxr::TfWeakBase
{
public:
    UsdNoticeListener();

    /**
     * @brief Handles USD object change notifications.
     * @param[in] objectsChanged The notification containing information about changed objects.
     */
    void handle(const pxr::UsdNotice::ObjectsChanged& objectsChanged);

    /**
     * @brief Enables or disables the listener.
     * @param[in] flag True to enable the listener, false to disable.
     */
    void enable(const bool& flag);

    /**
     * @brief Gets the map of deletion callbacks.
     * @return Reference to the map of deletion callbacks, keyed by callback ID.
     */
    std::map<int, std::function<void(const std::string&)>>& getDeletionCallbacks();

    /**
     * @brief Gets the map of physics scene addition callbacks.
     * @return Reference to the map of physics scene addition callbacks, keyed by callback ID.
     */
    std::map<int, std::function<void(const std::string&)>>& getPhysicsSceneAdditionCallbacks();

    /**
     * @brief Gets the map of physics scenes.
     * @return Reference to the map of physics scenes, keyed by their USD paths.
     */
    std::map<pxr::SdfPath, pxr::PhysxSchemaPhysxSceneAPI>& getPhysicsScenes();

    /**
     * @brief Gets the callback iteration counter.
     * @return Reference to the current callback iteration counter.
     */
    int& getCallbackIter();

private:
    /** @brief Map of physics scenes keyed by their USD paths */
    std::map<pxr::SdfPath, pxr::PhysxSchemaPhysxSceneAPI> m_physicsScenes;

    /** @brief Map of deletion callbacks keyed by callback ID */
    std::map<int, std::function<void(const std::string&)>> m_deletionCallbacks;

    /** @brief Map of physics scene addition callbacks keyed by callback ID */
    std::map<int, std::function<void(const std::string&)>> m_physicsSceneAdditionCallbacks;

    /** @brief Counter for generating unique callback IDs */
    int m_callbackIter;

    /** @brief Flag indicating whether the listener is enabled */
    bool m_enableFlag;
};

} // namespace isaacsim
} // namespace core
} // namespace simulation_manager
