# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Reference configured shelf and conveyor assets into the warehouse demo stage."""

from typing import Any

from .common import read_json, translate_rotate_scale_prim


def generate_shelves_assets(stage: Any, shelves_prim_path: Any, shelves_json_path: Any, shelves_asset_path: Any) -> Any:
    """Create shelf Xforms from JSON, reference their assets, and apply transforms.

    Args:
        stage: Stage where shelf prims are authored.
        shelves_prim_path: Parent path for generated shelf prims.
        shelves_json_path: Path to the shelf configuration JSON file.
        shelves_asset_path: Base asset path used with each shelf asset extension.

    Returns:
        None.
    """
    shelves_data = read_json(shelves_json_path)

    for shelf_id, shelf_details in shelves_data.items():

        shelf_stage_path = f"{shelves_prim_path}/{shelf_id}"

        shelf_asset_path = shelves_asset_path + shelf_details["asset_path_extension"]

        shelf_prim = stage.DefinePrim(shelf_stage_path, "Xform")
        shelf_prim.GetReferences().AddReference(shelf_asset_path)

        translate_rotate_scale_prim(
            stage=stage,
            prim=shelf_prim,
            translate_set=shelf_details["translation"],
            scale_set=shelf_details["scale"],
        )


def generate_conveyor_assets(
    stage: Any, conveyor_prim_path: Any, conveyor_json_path: Any, conveyor_asset_path: Any
) -> Any:
    """Create conveyor Xforms from JSON, reference their assets, and apply transforms.

    Args:
        stage: Stage where conveyor prims are authored.
        conveyor_prim_path: Parent path for generated conveyor prims.
        conveyor_json_path: Path to the conveyor configuration JSON file.
        conveyor_asset_path: Base asset path used with each conveyor asset extension.

    Returns:
        None.
    """
    conveyors_data = read_json(conveyor_json_path)

    for conveyor_id, conveyor_details in conveyors_data.items():

        conveyor_stage_path = f"{conveyor_prim_path}/{conveyor_id}"

        full_conveyor_asset_path = conveyor_asset_path + conveyor_details["asset_path_extension"]
        # print(full_conveyor_asset_path)

        conveyor_prim = stage.DefinePrim(conveyor_stage_path, "Xform")
        conveyor_prim.GetReferences().AddReference(full_conveyor_asset_path)

        translate_rotate_scale_prim(
            stage=stage,
            prim=conveyor_prim,
            translate_set=conveyor_details["translation"],
            rotate_set=conveyor_details["rotate"],
            scale_set=conveyor_details["scale"],
        )
