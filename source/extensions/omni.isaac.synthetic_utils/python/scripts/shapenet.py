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
import omni


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
    "bottle": "02876657",
    "bowl": "02880940",
    "earphone": "03261776",
    "mug": "03797390",
}

SYNSET_TO_LABEL = {v: k for k, v in LABEL_TO_SYNSET.items()}


async def convert(in_file, out_file, load_materials=False):
    # This import causes conflicts when global
    from omni.isaac import shapenet
    import omni.kit.tool.asset_importer.native_bindings as assetimport

    # A No-Material version of the omni.isaac.shapenet convert function
    # You really should only call this from the MainThread because there will be a deadlock on the GIL when this
    # calls C++ code from python.
    # flags can be OMNI_CONVERTER_FLAGS_IGNORE_ANIMATION, OMNI_CONVERTER_FLAGS_IGNORE_MATERIALS,
    #              OMNI_CONVERTER_FLAGS_SINGLE_MESH_FILE, or OMNI_CONVERTER_FLAGS_GEN_SMOOTH_NORMALS
    # print(in_file, ' is being converted and saved as ', out_file, ', please standby, and remember to tip your waitress.' )

    flags = assetimport.OMNI_CONVERTER_FLAGS_SINGLE_MESH_FILE
    if load_materials is False:
        flags = flags | assetimport.OMNI_CONVERTER_FLAGS_IGNORE_MATERIALS

    future = assetimport.omniConverterCreateUSD(in_file, out_file, flags)
    status = assetimport.OmniConverterStatus.eOK
    while True:
        status = assetimport.omniConverterCheckFutureStatus(future)
        if status == assetimport.OmniConverterStatus.eInProgress:
            await asyncio.sleep(0.1)
        else:
            break
    shapenet.g_futures_to_release.put(future)
    return status


def shapenet_convert(args):

    # This import needs to occur after kit is loaded so that physx can be discovered
    from omni.isaac import shapenet
    import omni.kit.tool.asset_importer.native_bindings as assetimport

    local_shapenet = shapenet.get_local_shape_loc()
    local_shapenet_output = f"{os.path.abspath(local_shapenet)}_nomat"
    if args.load_materials:
        local_shapenet_output = f"{os.path.abspath(local_shapenet)}_mat"
    os.makedirs(local_shapenet_output, exist_ok=True)

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
                print(f"max models ({args.max_models}) reached, exiting conversion")
                break
            local_path = os.path.join(local_shapenet, synset, model_id, "models/model_normalized.obj")

            shape_name = "model_normalized_nomat"
            if args.load_materials:
                shape_name = "model_normalized_mat"

            out_dir = os.path.join(local_shapenet_output, synset, model_id)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{shape_name}.usd")
            if not os.path.exists(out_path):
                status = asyncio.get_event_loop().run_until_complete(convert(local_path, out_path, args.load_materials))
                if not status == assetimport.OmniConverterStatus.eOK:
                    print(f"ERROR OmniConverterStatus is {status}")
                print(f"---Added {out_path}")
