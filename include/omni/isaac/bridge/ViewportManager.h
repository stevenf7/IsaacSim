// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <omni/kit/ViewportWindowUtils.h>

#include <string>
#include <unordered_map>

namespace omni
{
namespace isaac
{
namespace utils
{

using omni::kit::ExtensionWindowHandle;
using omni::kit::IViewport;
using omni::kit::IViewportWindow;

class ViewportManager
{
public:
    ViewportManager(IViewport* viewportIfacePtr)
    {
        mViewportInterface = viewportIfacePtr;
    }
    // Allows a REB component to claim a viewport
    bool registerViewport(std::string viewportName, std::string primPath)
    {
        if (mViewportHandles.find(viewportName) == mViewportHandles.end())
        {
            mViewportHandles.insert(std::make_pair(viewportName, primPath));
            return true;
        }
        return false;
    }
    // Allows a REB component to release a viewport
    bool unregisterViewport(std::string primPath)
    {

        for (auto it = mViewportHandles.begin(); it != mViewportHandles.end(); ++it)
        {
            if (it->second == primPath)
            {
                mViewportHandles.erase(it);
                return true;
            }
        }
        return false;
    }
    // Returns an existing viewport that is free
    std::string getFreeViewport()
    {
        size_t listSize = mViewportInterface->getViewportWindowInstanceCount();
        if (listSize > 0)
        {
            std::vector<ExtensionWindowHandle> windowList(listSize);
            if (mViewportInterface->getViewportWindowInstances(windowList.data(), listSize))
            {
                for (size_t i = 0; i < listSize; i++)
                {
                    const char* name = mViewportInterface->getViewportWindowName(windowList[i]);
                    std::string viewportName(name);
                    if (mViewportHandles.find(viewportName) == mViewportHandles.end())
                        return viewportName;
                }
            }
        }
        return "";
    }
    // Creates a new viewport
    std::string createNewViewport()
    {
        ExtensionWindowHandle newViewport = mViewportInterface->createViewportWindow();
        if (newViewport)
        {

            return std::string(mViewportInterface->getViewportWindowName(newViewport));
        }
        return "";
    }
    // Return an existing available viewport or creates a new one
    std::string getViewport()
    {
        std::string viewportWindowName = getFreeViewport();
        if (viewportWindowName == "")
            viewportWindowName = createNewViewport();
        return viewportWindowName;
    }
    void reset()
    {
        mViewportHandles.clear();
    }

private:
    IViewport* mViewportInterface;
    std::unordered_map<std::string, std::string> mViewportHandles;
};
}
}
}
