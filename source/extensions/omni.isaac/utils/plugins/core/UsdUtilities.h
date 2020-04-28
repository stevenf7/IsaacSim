#pragma once

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
}

}
}
}
