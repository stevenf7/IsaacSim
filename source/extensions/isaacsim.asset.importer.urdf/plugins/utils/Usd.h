// SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.
#include <pxr/pxr.h>
#include <pxr/usd/usd/stage.h>

/**
 * Select a existing layer as edit target.
 *
 * @param stage The stage of the operation.
 * @param layerIdentifier Layer identifier.
 * @return true if the layer is selected, false otherwise.
 *
 **/
static bool setAuthoringLayer(pxr::UsdStageRefPtr stage, const std::string& layerIdentifier)
{
    const auto& sublayer = pxr::SdfLayer::Find(layerIdentifier);
    if (!sublayer || !stage->HasLocalLayer(sublayer))
    {
        return false;
    }

    pxr::UsdEditTarget editTarget = stage->GetEditTargetForLocalLayer(sublayer);
    stage->SetEditTarget(editTarget);

    return true;
}
