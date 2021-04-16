#!/usr/bin/env python
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os
import pprint
from omni.isaac.python_app import OmniKitHelper
from omni.isaac.synthetic_utils import shapenet


"""Convert ShapeNetCore V2 to USD without materials.
By only converting the ShapeNet geometry, we can more quickly load assets into scenes for the purpose of creating
large datasets or for online training of Deep Learning models.
"""

if __name__ == "__main__":
    RENDER_CONFIG = {"experience": f'{os.environ["EXP_PATH"]}/isaac-sim.python.kit'}
    OmniKitHelper(config=RENDER_CONFIG)

    import argparse

    parser = argparse.ArgumentParser("Convert ShapeNet assets to USD")
    parser.add_argument(
        "--categories",
        type=str,
        nargs="+",
        default=None,
        help="List of ShapeNet categories to convert (space seperated).",
    )
    parser.add_argument(
        "--max-models", type=int, default=None, help="If specified, convert up to `max-models` per category."
    )
    parser.add_argument(
        "--load-materials", action="store_true", help="If specified, materials will be loaded from shapenet meshes"
    )
    args = parser.parse_args()

    if args.categories is None:
        print("The following categories and id's are supported:")
        pprint.pprint(shapenet.LABEL_TO_SYNSET)
        raise ValueError(f"No categories specified via --categories argument")
    # Ensure all categories specified are valid
    invalid_categories = []
    for c in args.categories:
        if c not in shapenet.LABEL_TO_SYNSET.keys() and c not in shapenet.LABEL_TO_SYNSET.values():
            invalid_categories.append(c)

    if invalid_categories:
        raise ValueError(f"The following are not valid ShapeNet categories: {invalid_categories}")

    # Ensure Omniverse Kit is launched via OmniKitHelper before shapenet_convert() is called
    shapenet.shapenet_convert(args)
