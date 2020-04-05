from pxr import Gf
import traceback
from .menu import ShapenetMenu
from .globals import *
from .shape import addShapePrim


def process_request_in_thread(thread_type, responses_queue, menu, request):
    response = {"success": True, "message": ""}
    if "synsetId" not in request:
        response["message"] += "No synsetId requested. "
        response["success"] = False
    else:
        synsetId = request["synsetId"]
        response["message"] += "synsetId = " + synsetId + ". "
    if "modelId" not in request:
        response["message"] += "No modelId requested. "
        response["success"] = False
    else:
        modelId = request["modelId"]
        response["message"] += "modelId = " + modelId + ". "

    # transfomrs have default values so are optional
    if "pos" not in request:
        pos = Gf.Vec3d(0, 0, 0)
    else:
        pos = Gf.Vec3d(request["pos"])
        response["message"] += f"pos = {pos}. "

    if "rot" not in request:
        rot = Gf.Rotation(Gf.Vec3d(0, 1, 0), 0)
    else:
        try:
            rot = Gf.Rotation(request["rot"][0], request["rot"][1])
            response["message"] += f"rot = {rot}. "
        except:
            rot = Gf.Rotation(Gf.Vec3d(0, 1, 0), 0)
            traceback.print_exc()

    if "scale" not in request:
        scale = 1.0
    else:
        scale = request["scale"]
        response["message"] += f"scale = {scale}. "

    # User can change some global variables with outside commands sent through here.
    global g_omni_shape_loc
    if "g_omni_shape_loc" in request:
        g_omni_shape_loc = request["g_omni_shape_loc"]
        response["message"] += f"g_omni_shape_loc = {g_omni_shape_loc}. "

    global g_local_shape_loc
    if "g_local_shape_loc" in request:
        g_local_shape_loc = request["g_local_shape_loc"]
        response["message"] += f"g_local_shape_loc = {g_local_shape_loc}. "

    global g_root_usd_namespace_path
    if "g_root_usd_namespace_path" in request:
        g_root_usd_namespace_path = request["g_root_usd_namespace_path"]
        response["message"] += f"g_root_usd_namespace_path = {g_root_usd_namespace_path}. "

    if "use_async" not in request:
        use_async = 1
    else:
        use_async = request["use_async"]
        response["message"] += f"use_async = {use_async}. "

    if "do_not_place" not in request:
        do_not_place = 0
    else:
        do_not_place = request["do_not_place"]
        response["message"] += f"do_not_place = {do_not_place}. "

    if response["success"]:
        try:
            # This is where all the work is done once the message is decoded.
            addShapePrimReturnMessage = addShapePrim(
                use_async, request["synsetId"], request["modelId"], pos, rot, scale, do_not_place
            )
            response["message"] += addShapePrimReturnMessage
        except:
            response["message"] += " had Error, so ould not run addShapePrim."
            response["success"] = False
            traceback.print_exc()

    responses_queue.put(response)
