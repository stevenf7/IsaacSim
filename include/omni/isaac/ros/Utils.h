// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <string>

namespace omni
{
namespace isaac
{
namespace ros_utils
{

/**
 * @brief Set prefixes to Ros topics and frameIds
 *
 * @param prefix rosNodePrefix
 * @param string_value rostopic or frameId string
 * @param is_rostopic Set true if string_value is a rostopic and false if string_value is a frameId
 *
 */

inline void addPrefix(const std::string& prefix, std::string& string_value, bool is_rostopic)
{

    if (prefix != "")
    {

        // Setting prefix to rostopics
        if (is_rostopic)
        {
            if (prefix[0] != '/')
            {
                string_value.insert(0, "/");
                string_value.insert(1, prefix);
            }
            else
            {
                string_value.insert(0, prefix);
            }
        }

        // Setting prefix to frameIds
        else
        {
            if (prefix[0] != '/')
            {
                string_value.insert(0, prefix);
                string_value.insert(prefix.length(), "/");
            }
            else
            {
                string_value.insert(0, prefix.substr(1));
                string_value.insert(prefix.substr(1).length(), "/");
            }
        }
    }
}

}
}
}
