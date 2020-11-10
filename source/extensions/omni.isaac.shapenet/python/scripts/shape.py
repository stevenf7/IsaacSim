import omni.assetimport
from omni.connection import OmniverseConnection
import omni.kit.connectionhub
import omni.kit.editor
import omni.usd

import asyncio
import json
import os
from pxr import UsdGeom, Gf, Tf
from queue import Queue

omni.kit.pipapi.install("requests")
import requests
import shutil
import sys
import threading

from .globals import *

# parse the text of a web pate and get the <a href="LINKS">Links</a>
def get_links(html):
    # Find the reference to <a href="
    found = html.find('<a href="')
    links = []
    while found > -1:
        q_loc = html.find('"', found + 9)
        links.append(html[found + 9 : q_loc])
        found = html.find('<a href="', found + 1)
    return links


def download_file(local_filename, url):
    with requests.get(url, stream=True) as r:
        with open(local_filename, "wb") as f:
            shutil.copyfileobj(r.raw, f)


# download all the files at url, which should be a director
# to the local folder
def download_folder(local_folder, url):
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)
    for href in get_links(requests.get(url).text):
        if not href[0] == "?":
            # not a reference to Name, Last Modified, Size, or Description
            if not href[0] == "/":
                # not the parent directory
                if href[-1] == "/":
                    # sub directory, add all files in it.
                    download_folder(local_folder + href, url + href)
                else:
                    print(f"--Downloading {url+href} to {local_folder + href}.")
                    download_file(local_folder + href, url + href)


def file_exists_on_omni(omni_path):
    if omni.assetimport.file_exists_on_omni(omni_path):
        return True
    return False


async def convert(in_file, out_file):
    # You really should only call this from the MainThread because there will be a deadlock on the GIL when this
    # calls C++ code from python.
    # flags can be OMNI_CONVERTER_FLAGS_IGNORE_ANIMATION, OMNI_CONVERTER_FLAGS_IGNORE_MATERIALS,
    #              OMNI_CONVERTER_FLAGS_SINGLE_MESH_FILE, or OMNI_CONVERTER_FLAGS_GEN_SMOOTH_NORMALS
    # print(in_file, " is being converted and saved as ", out_file, ", please standby, and remember to tip your waitress." )
    future = omni.assetimport.assetconverter.omniConverterCreateUSD(
        in_file,
        out_file,
        omni.assetimport.assetconverter.OMNI_CONVERTER_FLAGS_SINGLE_MESH_FILE
        | omni.assetimport.assetconverter.OMNI_CONVERTER_FLAGS_EXPORT_AS_SHAPENET,
    )
    status = omni.assetimport.assetconverter.OmniConverterStatus.eOK
    while True:
        status = omni.assetimport.assetconverter.omniConverterCheckFutureStatus(future)
        if status == omni.assetimport.assetconverter.OmniConverterStatus.eInProgress:
            await asyncio.sleep(0.1)
        else:
            break
    g_futures_to_release.put(future)
    return status


# This is the main entry point for any function that wants to add a shape to the scene.
# Care must be taken when running this on a seperate thread from the main thread because
# it calls c++ modules from python which hold the GIL.
def addShapePrim(use_async, synsetId, modelId, pos, rot, scale, do_not_place=False):
    # Get the local file system path and the omni server path
    shape_url = g_shapenet_url + synsetId + "/" + modelId + "/"
    local_folder = get_local_shape_loc() + "/" + synsetId + "/" + modelId + "/"
    local_path = local_folder + "models/model_normalized.obj"
    local_modified_path = local_folder + "models/modified/model.obj"
    omni_path = (
        g_omni_shape_loc + "/n" + synsetId + "/i" + modelId + "/"
    )  # don't forget to add the name at the end and .usd
    omni_modified_path = g_omni_shape_loc + "/n" + synsetId + "/i" + modelId + "/modified/"

    # Know we want to intorduce an instance of the shapenet model onto the stage.
    # Before we do that, we may have some work to do.
    editor_interface = omni.kit.editor.get_editor_interface()
    if not editor_interface:
        return "ERROR Could not get the editor interface from kit."
    if len(omni.kit.connectionhub.get_connection_hub_interface().get_connection_handles()) == 0:
        print("Kit must be connected to omniverse, and it is not.")
        return "ERROR Not Connected to Omniverse."

    stage = omni.usd.get_context().get_stage()
    if not stage:
        return "ERROR Could not get the stage."

    # Get the name of the shapenet object reference in the stage if it exists
    # (i.e. it has been added already and is used in another location on the stage).
    synsetID_path = g_root_usd_namespace_path + "/n" + synsetId
    over_path = synsetID_path + "/i" + modelId

    # Get the name of the instance we will add with the transform, this is the actual visible prim
    # instance of the reference to the omniverse file which was converted to local disk after
    global g_shapenet_db
    g_shapenet_db = get_database()
    shape_name = Tf.MakeValidIdentifier(g_shapenet_db[synsetId][modelId][4])
    if shape_name == "":
        shape_name = "mcarlson"
    prim_path = str(stage.GetDefaultPrim().GetPath()) + "/" + shape_name
    prim_path_len = len(prim_path)
    shape_name_len = len(shape_name)

    # if there is only one instance, we don't add a _# postfix, but if there is multiple, then the second instance
    # starts with a _1 postfix, and further additions increase that number.
    insta_count = 0
    while stage.GetPrimAtPath(prim_path):
        insta_count += 1
        prim_path = f"{prim_path[:prim_path_len]}_{insta_count}"
        shape_name = f"{shape_name[:shape_name_len]}_{insta_count}"

    omni_path = omni_path + shape_name + ".usd"
    omni_modified_path = omni_modified_path + shape_name + ".usd"
    # If the prim refernce to the omnivers file is not already on
    # the stage the stage we will need to add it.
    place_later = False
    if not stage.GetPrimAtPath(over_path):
        print(f"-Shapenet is adding {shape_name} to the stage for the first time.")
        # If the files does not already exist in omniverse we will have to add it there
        # with our automatic conversion of the original shapenet file.
        # We need to check if the modified file is on disk, so if it's not on the omni server it will
        # be added there even if the non modified one already exists on omni.
        if os.path.exists(local_modified_path) or file_exists_on_omni(omni_modified_path):
            omni_path = omni_modified_path
        if not file_exists_on_omni(omni_path):
            # If the original omniverse file does not exist locally, we will have to pull
            # it from Stanford's shapenet database on the web.
            if os.path.exists(local_modified_path):
                local_path = local_modified_path
                omni_path = omni_modified_path
            if not os.path.exists(local_path):
                # Pull the shapenet files to the local drive for conversion to omni:usd
                print(f"--Downloading {local_path} from {g_shapenet_url}.")
                download_folder(local_folder, shape_url)
            # Add The file to omniverse here, if you add them asyncronously, then you have to do the
            # rest of the scene adding later.
            print(f"---Converting {shape_name}...")
            if g_converters.empty() or not use_async:
                status = asyncio.get_event_loop().run_until_complete(convert(local_path, omni_path))
                if not status == omni.assetimport.assetconverter.OmniConverterStatus.eOK:
                    return f"ERROR OmniConverterStatus is {status}"
                print(f"---Added to Omniverse as {omni_path}.")
            else:
                print("---Added to Omniverse Asyncronously.")
                thread_num = g_converters.get()
                place_later = True
                # TODO Add thr running of the conversion in teh other thread, and when it is done, add to a queue
                # the addition of the over, and teh placement if it should be placed.

        # Add the over reference of the omni file to the stage here.
        print(f"----Adding over of {over_path} to stage.")
        if not do_not_place and not place_later:
            over = stage.OverridePrim(over_path)
            over.GetReferences().AddReference(omni_path)

    # Add the instance of the shape here.
    if not do_not_place and not place_later:
        prim = stage.DefinePrim(prim_path, "Xform")
        prim.GetReferences().AddInternalReference(over_path)

        metersPerUnit = UsdGeom.GetStageMetersPerUnit(stage)
        scaled_scale = scale / metersPerUnit
        addobject_fn(prim.GetPath(), pos, rot, scaled_scale)
        return "Added object."

    return "Didn't add object."


def get_min_max_vert(obj_file_name):
    min_x = min_y = min_z = sys.float_info.max
    max_x = max_y = max_z = -sys.float_info.max
    with open(obj_file_name, "r") as fi:
        for ln in fi:
            if ln.startswith("v "):
                vx = float(ln[2:].partition(" ")[0])
                vy = float(ln[2:].partition(" ")[2].partition(" ")[0])
                vz = float(ln[2:].partition(" ")[2].partition(" ")[2])
                min_x = min(min_x, vx)
                min_y = min(min_y, vy)
                min_z = min(min_z, vz)
                max_x = max(max_x, vx)
                max_y = max(max_y, vy)
                max_z = max(max_z, vz)
    return Gf.Vec3f(min_x, min_y, min_z), Gf.Vec3f(max_x, max_y, max_z)


# Got this From Lou Rohan... Thanks Lou!
# objectpath - path in omniverse - omni:/Projects/Siggraph2019/AtticWorkflow/Props/table_cloth/table_cloth.usd
# objectname - name you want it to be called in the stage
# xform - Gf.Matrix4d
def addobject_fn(path, position, rotation, scale):
    # The original model was translated by the centroid, and scaled to be normalized by the length of the
    # hypotenuse of the bbox
    translate_mtx = Gf.Matrix4d()
    rotate_mtx = Gf.Matrix4d()
    scale_mtx = Gf.Matrix4d()

    translate_mtx.SetTranslate(position)  # centroid/metersPerUnit)
    rotate_mtx.SetRotate(rotation)
    scale_mtx = scale_mtx.SetScale(scale)
    transform_matrix = scale_mtx * rotate_mtx * translate_mtx

    omni.kit.commands.execute("TransformPrimCommand", path=path, new_transform_matrix=transform_matrix)
