// SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#pragma once

#include <carb/InterfaceUtils.h>
#include <carb/logging/Log.h>

// clang-format off
#include <omni/usd/UsdContextIncludes.h>
#include <omni/usd/UtilsIncludes.h>
// clang-format on

#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdUtils.h>

#include <chrono>
#include <iostream>
#include <string>

#include <omni/usd-abi/IRenderProductPrim.h>

namespace isaacsim
{
namespace core
{
namespace includes
{

/**
 * @brief Token for overriding prim names in Isaac Sim.
 * @details Used to specify custom names for prims that differ from their USD names.
 */
static const PXR_NS::TfToken g_kIsaacNameOveride("isaac:nameOverride");

/**
 * @brief Retrieves the camera prim associated with a render product.
 * @details
 * Looks up the camera prim referenced by a render product in the current USD stage.
 * The function performs several validation steps:
 * 1. Checks for valid stage and interfaces
 * 2. Creates render product prim handle
 * 3. Extracts camera path and retrieves corresponding prim
 *
 * @param[in] renderProductPathString Path to the render product as a string
 * @return pxr::UsdPrim Camera prim if found, invalid prim otherwise
 *
 * @note Returns invalid prim if any required component is missing
 * @warning Requires valid USD context and stage
 */
inline pxr::UsdPrim getCameraPrimFromRenderProduct(const std::string& renderProductPathString)
{
    pxr::UsdStagePtr stage = omni::usd::UsdContext::getContext()->getStage();
    omni::usd::IPathAbi* iPath = carb::getCachedInterface<omni::usd::IPathAbi>();
    omni::usd::IRenderProductPrimFactory* iPrimFactory = carb::getCachedInterface<omni::usd::IRenderProductPrimFactory>();
    if (!stage || !iPath || !iPrimFactory)
    {
        return pxr::UsdPrim();
    }
    omni::usd::PathH renderProductPathH = iPath->getHandle(renderProductPathString.c_str());
    omni::usd::IRenderProductPrimPtr rp =
        iPrimFactory->createPrimFromStage(omni::usd::UsdContext::getContext()->getStageId(), renderProductPathH);
    if (!rp)
    {
        return pxr::UsdPrim();
    }
    return stage->GetPrimAtPath(pxr::SdfPath(iPath->getText(rp->getCameraPath())));
}

/**
 * @brief Retrieves a specific attribute from a camera associated with a render product.
 * @details
 * Combines camera prim lookup with attribute access in a single function.
 * Process:
 * 1. Gets the camera prim from render product
 * 2. Validates the camera prim
 * 3. Retrieves the requested attribute
 *
 * @param[in] attributeString Name of the attribute to retrieve
 * @param[in] renderProductPathString Path to the render product
 * @return pxr::UsdAttribute The requested attribute if found, invalid attribute otherwise
 *
 * @note Returns invalid attribute if camera prim is invalid
 * @see getCameraPrimFromRenderProduct
 */
inline pxr::UsdAttribute getCameraAttributeFromRenderProduct(const std::string& attributeString,
                                                             const std::string& renderProductPathString)
{
    pxr::UsdPrim cameraPrim = getCameraPrimFromRenderProduct(renderProductPathString);
    if (!cameraPrim.IsValid())
    {
        return pxr::UsdAttribute();
    }
    return cameraPrim.GetAttribute(pxr::TfToken(attributeString.c_str()));
}

/**
 * @brief Safely retrieves a USD attribute value with error handling.
 * @details
 * Provides a safe way to get attribute values with:
 * - Value existence checking
 * - Warning messages for missing values
 * - Type-safe value retrieval
 *
 * @tparam T Type of the attribute value to retrieve
 * @param[in] attr USD attribute to read
 * @param[out] inputValue Variable to store the attribute value
 *
 * @note Logs a warning if attribute exists but has no value
 * @warning Input value remains unchanged if attribute has no value
 */
template <class T>
void safeGetAttribute(const pxr::UsdAttribute& attr, T& inputValue)
{

    if (attr.HasValue())
    {
        attr.Get(&inputValue);
    }
    else
    {
        CARB_LOG_WARN("USD attribute %s does not exist, using default", attr.GetName().GetString().c_str());
    }
}

/**
 * @brief Retrieves the name of a USD prim, with support for custom overrides.
 * @details
 * Determines the name of a prim by:
 * 1. Using the default prim name from USD
 * 2. Checking for "isaac:nameOverride" attribute to allow custom naming
 * 3. Using the override value if present
 *
 * @param[in] prim USD prim whose name to retrieve
 * @return std::string Name of the prim, potentially from override attribute
 *
 * @see g_kIsaacNameOveride
 * @see safeGetAttribute
 */
inline std::string getName(const pxr::UsdPrim& prim)
{
    std::string primName = prim.GetName().GetString();
    if (prim.HasAttribute(g_kIsaacNameOveride))
    {
        safeGetAttribute<std::string>(prim.GetAttribute(g_kIsaacNameOveride), primName);
    }
    return primName;
}

/**
 * @brief Converts a uint64_t token to a USD path.
 * @details
 * Performs a reinterpret cast from uint64_t to SdfPath with:
 * - Platform-specific warning suppression
 * - Safe type conversion
 *
 * @param[in] pathToken Path token as uint64_t
 * @return pxr::SdfPath Converted USD path
 *
 * @warning Uses reinterpret_cast, ensure token is a valid path representation
 */
inline pxr::SdfPath getSdfPathFromUint64(uint64_t pathToken)
{
#if defined(_WIN32)
#    pragma warning(push)
#    pragma warning(disable : 4996)
    return reinterpret_cast<const pxr::SdfPath&>(pathToken);
#    pragma warning(pop)
#else
#    pragma GCC diagnostic push
#    pragma GCC diagnostic ignored "-Wstrict-aliasing"
    return reinterpret_cast<const pxr::SdfPath&>(pathToken);
#    pragma GCC diagnostic pop
#endif
}

} // namespace includes
} // namespace core
} // namespace isaacsim
