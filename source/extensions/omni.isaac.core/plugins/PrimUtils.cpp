// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


// clang-format off
#include <UsdPCH.h>
#include <pxr/base/tf/patternMatcher.h>
// clang-format on

#include <PrimUtils.h>

void omni::isaac::core::findMatchingChildren(pxr::UsdPrim root,
                                             const std::string& pattern,
                                             std::vector<pxr::UsdPrim>& primsRet)
{
    if (!root)
    {
        return;
    }

    pxr::TfPatternMatcher matcher(pattern, true, true);
    pxr::UsdPrimSiblingRange range = root.GetAllChildren();
    for (auto child : range)
    {
        if (matcher.Match(child.GetName()))
        {
            primsRet.push_back(child);
        }
    }
}


std::vector<std::string> omni::isaac::core::findMatchingPrimPaths(const std::string& pattern, long int stageId)
{
    pxr::UsdStageRefPtr stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
    if (!stage)
    {
        throw std::invalid_argument("stage id doesn't correspond to an existing stage");
    }

    std::string trimmedPattern = pxr::TfStringTrim(pattern, "/");
    std::vector<std::string> tokens = pxr::TfStringSplit(trimmedPattern, "/");

    // need to wrap the token patterns in '^' and '$' to prevent matching anywhere in the string
    for (std::string& tok : tokens)
    {
        tok = '^' + tok + '$';
    }

    std::vector<pxr::UsdPrim> roots;
    std::vector<pxr::UsdPrim> matches;
    std::vector<std::string> pathsRet;

    roots.push_back(stage->GetPseudoRoot());

    int numTokens = int(tokens.size());

    for (int i = 0; i < numTokens; i++)
    {
        for (auto& prim : roots)
        {
            findMatchingChildren(prim, tokens[i], matches);
        }

        if (i < numTokens - 1)
        {
            std::swap(roots, matches);
            matches.clear();
        }
    }

    for (auto& prim : matches)
    {
        pathsRet.push_back(prim.GetPrimPath().GetString());
    }

    return pathsRet;
}
