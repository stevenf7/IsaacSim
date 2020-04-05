import carb.tokens

from queue import Queue
import os
import bz2

try:
    import cPickle as pickle
except:
    import pickle

g_bind_address = ("localhost", "8080")
g_omni_shape_loc = "omni:/Projects/shapenet"
g_local_shape_loc = None
g_root_usd_namespace_path = "/shapenet"
g_shapenet_url = "http://shapenet.cs.stanford.edu/shapenet/obj-zip/ShapeNetCore.v2/"

g_futures_to_release = Queue()
g_num_converters = 0
g_converters = Queue()
g_converter_loops = []
g_converter_threads = []
g_shapenet_db = None


def get_database():
    global g_shapenet_db
    if g_shapenet_db == None:
        f = bz2.BZ2File(os.path.dirname(os.path.realpath(__file__)) + "/shapenet_db2.pickle.bz2", "rb")
        g_shapenet_db = pickle.load(f)
        f.close()
        # Shapenet v1, where the db comes from, has a few extra models that v2 has not converted.
        # TODO make it download shapenet 1 models, normalize them, and put them in.
        # For now we will just remove those.
        del g_shapenet_db["02834778"]
        del g_shapenet_db["02858304"]

    return g_shapenet_db


def get_local_shape_loc():
    global g_local_shape_loc
    if g_local_shape_loc == None:

        env_path = os.getenv("SHAPENET_LOCAL_DIR")
        if env_path == None:
            resolved_data_path = carb.tokens.get_tokens_interface().resolve("${data}")
            g_local_shape_loc = resolved_data_path + "\shapenet"
            print(f"env var SHAPENET_LOCAL_DIR not set, using default data dir {g_local_shape_loc}")
        else:
            g_local_shape_loc = env_path
    return g_local_shape_loc
