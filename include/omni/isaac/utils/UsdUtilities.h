// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/InterfaceUtils.h>
#include <carb/logging/Log.h>

#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdUtils.h>

#include <chrono>
#include <iostream>
#include <string>

#include <omni/usd-abi/IRenderProductPrim.h>
namespace omni
{
namespace isaac
{
namespace utils
{

static const PXR_NS::TfToken kIsaacNameOveride("isaac:nameOverride");

inline pxr::UsdAttribute getCameraAttributeFromRenderProduct(const std::string& attributeString,
                                                             const std::string& renderProductPathString)
{
    pxr::UsdStagePtr stage = omni::usd::UsdContext::getContext()->getStage();
    omni::usd::IPathAbi* iPath = carb::getCachedInterface<omni::usd::IPathAbi>();
    omni::usd::IRenderProductPrimFactory* iPrimFactory = carb::getCachedInterface<omni::usd::IRenderProductPrimFactory>();
    if (!stage || !iPath || !iPrimFactory)
        return pxr::UsdAttribute();
    omni::usd::PathH renderProductPathH = iPath->getHandle(renderProductPathString.c_str());
    omni::usd::IRenderProductPrimPtr rp =
        iPrimFactory->createPrimFromStage(omni::usd::UsdContext::getContext()->getStageId(), renderProductPathH);
    if (!rp)
        return pxr::UsdAttribute();
    pxr::UsdPrim cameraPrim = stage->GetPrimAtPath(pxr::SdfPath(iPath->getText(rp->getCameraPath())));
    if (!cameraPrim.IsValid())
        return pxr::UsdAttribute();
    return cameraPrim.GetAttribute(pxr::TfToken(attributeString.c_str()));
}

template <class T>
void safeGetAttribute(const pxr::UsdAttribute& attr, T& inputValue)
{
    if (attr.IsValid())
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
    else
    {
        CARB_LOG_ERROR_ONCE(
            "USD attribute is INVALID, you will only be warned once, so you probably want to fix whatever called "
            "omni::isaac::utils::safeGetAttribute");
    }
}

inline std::string GetName(const pxr::UsdPrim& prim)
{
    std::string primName = prim.GetName().GetString();
    if (prim.HasAttribute(kIsaacNameOveride))
    {
        safeGetAttribute<std::string>(prim.GetAttribute(kIsaacNameOveride), primName);
    }
    return primName;
}


}
}
}
