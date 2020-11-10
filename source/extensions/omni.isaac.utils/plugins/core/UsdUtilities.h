#pragma once

#include <carb/logging/Log.h>

#include <chrono>
#include <iostream>
#include <string>
namespace omni
{
namespace isaac
{
namespace utils
{

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

}
}
}
