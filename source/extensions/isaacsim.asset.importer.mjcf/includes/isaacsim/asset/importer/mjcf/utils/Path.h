// SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#pragma once

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <carb/logging/Log.h>

#include <OmniClient.h>
#include <string>


// Platform-specific headers
#ifdef _WIN32
#    include <filesystem>
#else
#    include <sys/stat.h>
#endif

namespace isaacsim
{
namespace asset
{
namespace utils
{
namespace path
{
inline bool isFile(const std::string& path)
{
#ifdef _WIN32
    namespace fs = std::filesystem;

    return fs::is_regular_file(path); // Checks if the path is a regular file

#else
    // POSIX/Unix-like systems implementation
    struct stat pathStat;
    if (stat(path.c_str(), &pathStat) != 0)
    {
        // Path does not exist
        return false;
    }
    // Check if it's a regular file
    return S_ISREG(pathStat.st_mode);
#endif
}


inline std::string normalizeUrl(const char* url)
{
    std::string ret;
    char stringBuffer[1024];
    std::unique_ptr<char[]> stringBufferHeap;
    size_t bufferSize = sizeof(stringBuffer);
    const char* normalizedUrl = omniClientNormalizeUrl(url, stringBuffer, &bufferSize);
    if (!normalizedUrl)
    {
        stringBufferHeap = std::unique_ptr<char[]>(new char[bufferSize]);
        normalizedUrl = omniClientNormalizeUrl(url, stringBufferHeap.get(), &bufferSize);
        if (!normalizedUrl)
        {
            normalizedUrl = "";
            CARB_LOG_ERROR("Cannot normalize %s", url);
        }
    }

    ret = normalizedUrl;
    for (auto& c : ret)
    {
        if (c == '\\')
        {
            c = '/';
        }
    }
    return ret;
}

inline std::string resolve_absolute(std::string parent, std::string relative)
{
    size_t bufferSize = parent.size() + relative.size();
    std::unique_ptr<char[]> stringBuffer = std::unique_ptr<char[]>(new char[bufferSize]);
    std::string combined_url = normalizeUrl((parent + "/" + relative).c_str());
    return combined_url;
}


// Helper function to split a path into components
inline std::vector<std::string> split_path(const std::string& path)
{
    std::vector<std::string> components;
    size_t start = 0;
    size_t end = path.find('/');
    while (end != std::string::npos)
    {
        components.push_back(path.substr(start, end - start));
        start = end + 1;
        end = path.find('/', start);
    }
    components.push_back(path.substr(start));
    return components;
}

/**
 * Calculates the relative path of target relative to base.
 *
 * @param base The base path.
 * @param target The target path.
 * @return The relative path of target relative to base.
 * @throws std::invalid_argument If base or target is not a valid path.
 */
inline std::string resolve_relative(const std::string& base, const std::string& target)
{

    if (!isFile(target))
    {
        return target;
    }
    // Normalize both paths to use '/' as the separator
    std::string base_normalized = normalizeUrl(base.c_str());
    std::string target_normalized = normalizeUrl(target.c_str());

    // Split both paths into components
    std::vector<std::string> base_components = split_path(base_normalized);
    std::vector<std::string> target_components = split_path(target_normalized);

    if (isFile(base_normalized))
    {
        base_components.pop_back();
    }

    // Find the common prefix
    size_t common_prefix_length = 0;
    while (common_prefix_length < base_components.size() && common_prefix_length < target_components.size() &&
           base_components[common_prefix_length] == target_components[common_prefix_length])
    {
        common_prefix_length++;
    }

    // Calculate the relative path
    std::string relative_path;
    for (size_t i = common_prefix_length; i < base_components.size(); i++)
    {
        relative_path += "../";
    }
    for (size_t i = common_prefix_length; i < target_components.size(); i++)
    {
        relative_path += target_components[i] + "/";
    }

    // Remove the trailing '/'
    if (!relative_path.empty() && relative_path.back() == '/')
    {
        relative_path.pop_back();
    }

    return relative_path;
}

/**
 * Calculates the final path by resolving the relative path and removing any unnecessary components.
 *
 * @param path The input path string.
 * @return The computed final path.
 * @throws std::invalid_argument If the path is not a valid path.
 */
inline std::string resolve_path(const std::string& path)
{
    // Normalize the path to use '/' as the separator
    std::string normalized_path = normalizeUrl(path.c_str());

    // Split the path into components
    std::vector<std::string> components = split_path(normalized_path);

    // Resolve the relative path
    std::vector<std::string> resolved_components;
    for (const std::string& component : components)
    {
        if (component == "..")
        {
            if (!resolved_components.empty())
            {
                resolved_components.pop_back();
            }
        }
        else if (component != "." && component != "")
        {
            resolved_components.push_back(component);
        }
    }

    // Reconstruct the final path
    std::string final_path;
    if (path[0] == '/')
    {
        final_path += "/";
    }
    for (const std::string& component : resolved_components)
    {
        final_path += component + "/";
    }

    // Remove the trailing '/'
    if (!final_path.empty() && final_path.back() == '/')
    {
        final_path.pop_back();
    }

    return final_path;
}

// given the path of one file it strips the filename and appends the relative
// path onto it
inline std::string MakeRelativePath(const std::string& filePath, const std::string& fileRelativePath)
{
    // get base path of file
    size_t lastSlashPos = filePath.find_last_of("/\\");
    std::string basePath;

    if (lastSlashPos != std::string::npos)
    {
        basePath = filePath.substr(0, lastSlashPos + 1);
    }

    std::string adjustedRelativePath = fileRelativePath;

    // Remove leading slash or backslash if present
    if (!adjustedRelativePath.empty() && (adjustedRelativePath[0] == '\\' || adjustedRelativePath[0] == '/'))
    {
        adjustedRelativePath = adjustedRelativePath.substr(1);
    }

    // Combine the base path with the adjusted relative path
    return basePath + adjustedRelativePath;
}

inline std::string pathJoin(const std::string& path1, const std::string& path2)
{
    if (path1.empty())
    {
        return path2;
    }
    else
    {
        auto last = path1.rbegin();
#ifdef _WIN32
        if (*last != '/' && *last != '\\')
#else
        if (*last != '/')
#endif
        {
            return path1 + '/' + path2;
        }
        else
        {
            return path1 + path2;
        }
    }
}


inline std::string getPathStem(const char* path)
{
    if (!path || !*path)
    {
        return "";
    }

    const char* p = strrchr(path, '/');
#ifdef _WIN32
    const char* q = strrchr(path, '\\');
    if (q > p)
    {
        p = q;
    }
#endif

    const char* fnameStart = p ? p + 1 : path;
    const char* ext = strrchr(fnameStart, '.');
    if (ext)
    {
        return std::string(fnameStart, ext);
    }
    else
    {
        return fnameStart;
    }
}

inline std::string getParent(const std::string& filePath)
{
    size_t found = filePath.find_last_of("/\\");
    if (found != std::string::npos)
    {
        return filePath.substr(0, found);
    }
    return "";
}

} // namespace path
} // namespace utils
} // namespace isaac
} // namespace omni
