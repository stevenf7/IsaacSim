# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import os

import omni
from omni.client._omniclient import Result
from omni.kit.widget.stage.stage_model import AssetType
from pxr import Sdf, UsdUtils


def join(base, name):
    if base.startswith("omniverse://"):
        if name.startswith("./"):
            name = name[2:]
        while name.startswith("../"):
            base = os.path.dirname(base)
            name = name[3:]
        if base.endswith("/"):
            base = base[:-1]
        return base + "/" + name
    else:
        return os.path.join(base, name)


async def list_sub_files(abs_path, filter_fn=lambda a: True):
    sub_folders = []
    remaining_folders = []
    remaining_folders.extend(abs_path)
    files = []
    while len(remaining_folders):
        path = remaining_folders.pop()
        result, entries = await asyncio.wait_for(omni.client.list_async(path), timeout=10)
        if result == Result.OK:
            files = files + [
                join(path, e.relative_path) for e in entries if (e.flags & 4) == 0 and filter_fn(e.relative_path)
            ]
            remaining_folders = remaining_folders + [join(path, e.relative_path) for e in entries if (e.flags & 4) > 0]
    return files


def list_references(stage_path, resolve_relatives=True):

    (all_layers, all_assets, unresolved_paths) = UsdUtils.ComputeAllDependencies(stage_path)
    paths = []

    def add_path(path):
        paths.append(path)
        return path

    if resolve_relatives:
        for layer in all_layers:
            UsdUtils.ModifyAssetPaths(layer, add_path)
    else:
        paths = [str(layer).split("'")[1] for layer in all_layers]
    paths = list(set(paths))
    return paths


def isabs(path):
    if path.lower().startswith("omniverse://"):
        return True
    if path.lower().startswith("file://"):
        return True
    return os.path.isabs(path)


def filter_usd(item) -> bool:
    _, ext = os.path.splitext(item)
    if ext in [".usd", ".usda", ".usdc", ".usdz"]:
        return True
    return False


def filter_mdl(item) -> bool:
    _, ext = os.path.splitext(item)
    if ext in [".mdl"]:
        return True
    return False


async def check_for_abs_paths(base_path):
    abs_items = {}
    files = await list_sub_files(base_path, filter_usd)
    i = 0
    for item in files:
        print(f"check {i}/{len(files)}")
        abs_refs = [i for i in list_references(item) if isabs(i)]
        if len(abs_refs):
            abs_items[item] = abs_refs
        i = i + 1
    return abs_items


def is_external(path, base_path):
    # if not isabs(path):
    #     path = os.path.join(parent, path)
    # -1 because os module removes second slash on omniverse://
    try:
        return len(os.path.commonpath([path, base_path])) != (len(base_path) - 1)
    except:
        print(path, base_path)
        raise Exception


async def check_for_external_refs(base_path):
    abs_items = {}
    for item in await list_sub_files(base_path, filter_usd):
        parent = os.path.dirname(item)
        abs_refs = [i for i in list_references(item, resolve_relatives=False) if is_external(i, base_path)]
        if len(abs_refs):
            abs_items[item] = abs_refs
    return abs_items


async def get_assets_ref_count(base_path):
    items = {item: 0 for item in await list_sub_files(base_path)}
    for item in items.keys():
        print(item)
        for i in list_references(item):
            base = os.path.dirname(item)
            name = join(base, i)
            print(" ", name)
            if name in items:
                items[name] += 1
    items = {k: v for k, v in sorted(items.items(), key=lambda item: item[1])}
    return items


def check_for_missing_refs(base_path):
    items = {item: 0 for item in list_sub_files(base_path, filter_usd)}
    for item in items.keys():
        (all_layers, all_assets, unresolved_paths) = UsdUtils.ComputeAllDependencies(item)
        if len(unresolved_paths) > 0:
            print(item, unresolved_paths)


async def check_if_exists(path):
    result, _ = await omni.client.stat_async(path)
    if result == Result.OK:
        return True
    else:
        return False


def has_missing_reference_in_layer(layer_identifier):
    queue = [layer_identifier]
    accessed_layers = []
    while len(queue) > 0:
        identifier = queue.pop(0)
        if identifier in accessed_layers:
            continue

        accessed_layers.append(identifier)
        layer = Sdf.Layer.FindOrOpen(identifier)
        if layer:
            for reference in layer.externalReferences:
                if len(reference) > 0:
                    absolute_path = layer.ComputeAbsolutePath(reference)
                    queue.append(absolute_path)
        else:
            return True

    return False


def has_missing_specifier(prim_spec):
    reference_list = prim_spec.referenceList
    items = reference_list.GetAddedOrExplicitItems()
    for item in items:
        if item.assetPath:
            filename = item.assetPath
            if AssetType().is_usd(filename):
                filename = prim_spec.layer.ComputeAbsolutePath(filename)
                if has_missing_reference_in_layer(filename):
                    return True

    return False


def has_missing_reference(prim):
    for prim_spec in prim.GetPrimStack():
        if has_missing_specifier(prim_spec):
            return True

    return False
