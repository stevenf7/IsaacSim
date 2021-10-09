// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once
namespace omni
{
namespace isaac
{
namespace utils
{
namespace tools
{
/**
 * @brief Check if a prim has a specific schema
 *
 * @param prim
 * @param name
 * @return true if schema exists on prim
 * @return false if schema does not exist on prim
 */
inline bool hasSchema(const pxr::UsdPrim& prim, const pxr::TfToken& name)
{
    pxr::TfTokenVector schemas = prim.GetAppliedSchemas();
    for (size_t i = 0; i < schemas.size(); ++i)
    {
        if (schemas[i] == name)
            return true;
    }

    return false;
}

/**
 * @brief Print all attributes of prim
 *
 * @param prim
 */
inline void printAttributes(const pxr::UsdPrim& prim)
{
    std::vector<pxr::UsdAttribute> attrs = prim.GetAttributes();
    CARB_LOG_ERROR("Prim: %s", prim.GetName().GetString().c_str());
    for (size_t j = 0; j < attrs.size(); j++)
    {
        CARB_LOG_ERROR("   ATTR: %s", attrs[j].GetName().GetString().c_str());
    }
}
/**
 * @brief Print all properties of prim
 *
 * @param prim
 */
inline void printProperties(const pxr::UsdPrim& prim)
{
    std::vector<pxr::UsdProperty> props = prim.GetProperties();
    CARB_LOG_ERROR("Prim: %s", prim.GetName().GetString().c_str());
    for (size_t j = 0; j < props.size(); j++)
    {
        CARB_LOG_ERROR("   PROP: %s", props[j].GetName().GetString().c_str());
    }
}

/**
 * @brief Print all children of prim
 *
 * @param prim
 */
inline void printChildren(const pxr::UsdPrim& prim)
{
    pxr::UsdPrimSiblingRange range = prim.GetAllChildren();

    for (pxr::UsdPrimSiblingRange::iterator iter = range.begin(); iter != range.end(); ++iter)
    {
        pxr::UsdPrim prim = *iter;
        CARB_LOG_ERROR("   CHILD: %s", prim.GetName().GetString().c_str());
    }
}

/**
 * @brief Print attributes, properties for prim and its children
 *
 * @param prim
 */
inline void printAllPrimInfo(const pxr::UsdPrim& prim)
{
    printAttributes(prim);
    printProperties(prim);
    pxr::UsdPrimSiblingRange range = prim.GetAllChildren();
    for (pxr::UsdPrimSiblingRange::iterator iter = range.begin(); iter != range.end(); ++iter)
    {
        pxr::UsdPrim prim = *iter;
        printAttributes(prim);
        printProperties(prim);
    }
}
}
}
}
}
