#!/usr/bin/env python
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import os
import asyncio
import omni.kit.pipapi
import omni
import omni.kit.app
from omni_dl_examples.helpers import OmniKitHelper


"""Convert ShapeNetCore V2 to USD without materials.
By only converting the ShapeNet geometry, we can more quickly load assets into scenes for the purpose of creating
large datasets or for online training of Deep Learning models.
"""


LABEL_TO_SYNSET = {
    "table": "04379243",
    "monitor": "03211117",
    "phone": "04401088",
    "watercraft": "04530566",
    "chair": "03001627",
    "lamp": "03636649",
    "speaker": "03691459",
    "bench": "02828884",
    "plane": "02691156",
    "bathtub": "02808440",
    "bookcase": "02871439",
    "bag": "02773838",
    "basket": "02801938",
    "bowl": "02880940",
    "bus": "02924116",
    "cabinet": "02933112",
    "camera": "02942699",
    "car": "02958343",
    "dishwasher": "03207941",
    "file": "03337140",
    "knife": "03624134",
    "laptop": "03642806",
    "mailbox": "03710193",
    "microwave": "03761084",
    "piano": "03928116",
    "pillow": "03938244",
    "pistol": "03948459",
    "printer": "04004475",
    "rocket": "04099429",
    "sofa": "04256520",
    "washer": "04554684",
    "rifle": "04090263",
    "can": "02946921",
}

SYNSET_TO_LABEL = {v: k for k, v in LABEL_TO_SYNSET.items()}


async def convert_nomat(in_file, out_file):
    # This import causes conflicts when global
    from omni.isaac import shapenet

    # A No-Material version of the omni.isaac.shapenet convert function
    # You really should only call this from the MainThread because there will be a deadlock on the GIL when this
    # calls C++ code from python.
    # flags can be OMNI_CONVERTER_FLAGS_IGNORE_ANIMATION, OMNI_CONVERTER_FLAGS_IGNORE_MATERIALS,
    #              OMNI_CONVERTER_FLAGS_SINGLE_MESH_FILE, or OMNI_CONVERTER_FLAGS_GEN_SMOOTH_NORMALS
    # print(in_file, ' is being converted and saved as ', out_file, ', please standby, and remember to tip your waitress.' )
    future = omni.assetimport.assetconverter.omniConverterCreateUSD(
        in_file,
        out_file,
        omni.assetimport.assetconverter.OMNI_CONVERTER_FLAGS_IGNORE_MATERIALS
        | omni.assetimport.assetconverter.OMNI_CONVERTER_FLAGS_SINGLE_MESH_FILE,
    )
    status = omni.assetimport.assetconverter.OmniConverterStatus.eOK
    while True:
        status = omni.assetimport.assetconverter.omniConverterCheckFutureStatus(future)
        if status == omni.assetimport.assetconverter.OmniConverterStatus.eInProgress:
            await asyncio.sleep(0.1)
        else:
            break
    shapenet.g_futures_to_release.put(future)
    return status


def shapenet_convert_nomat(args):
    # This import causes conflicts when global
    from omni.isaac import shapenet

    OmniKitHelper()

    local_shapenet = shapenet.get_local_shape_loc()
    local_shapenet_nomat = f"{os.path.abspath(local_shapenet)}_nomat"
    os.makedirs(local_shapenet_nomat, exist_ok=True)

    synsets = args.categories
    if synsets is None:
        synsets = LABEL_TO_SYNSET.values()

    for synset in synsets:
        print(f"\nConverting synset {synset}...")
        # If synset is specified by label, convert to synset
        if synset in LABEL_TO_SYNSET:
            synset = LABEL_TO_SYNSET[synset]

        model_dirs = os.listdir(os.path.join(local_shapenet, synset))
        for i, model_id in enumerate(model_dirs):
            if i >= args.max_models:
                break
            local_path = os.path.join(local_shapenet, synset, model_id, "models/model_normalized.obj")

            shape_name = "model_normalized_nomat"
            out_dir = os.path.join(local_shapenet_nomat, synset, model_id)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{shape_name}.usd")
            if not os.path.exists(out_path):
                status = asyncio.get_event_loop().run_until_complete(convert_nomat(local_path, out_path))
                if not status == omni.assetimport.assetconverter.OmniConverterStatus.eOK:
                    print(f"ERROR OmniConverterStatus is {status}")
                print(f"---Added {out_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser("Convert ShapeNet assets to USD without material")
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
    args = parser.parse_args()

    # Ensure all categories specified are valid
    invalid_categories = []
    for c in args.categories:
        if c not in LABEL_TO_SYNSET.keys() and c not in LABEL_TO_SYNSET.values():
            invalid_categories.append(c)

    if invalid_categories:
        raise ValueError(f"The following are not valid ShapeNet categories: {invalid_categories}")

    shapenet_convert_nomat(args)
