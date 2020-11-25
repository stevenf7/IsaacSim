import carb.tokens

from queue import Queue
import os
import bz2

try:
    import cPickle as pickle
except:
    import pickle

g_bind_address = ("localhost", "7011")
g_omni_shape_loc = "/Projects/shapenet"
g_local_shape_loc = None
g_root_usd_namespace_path = "/shapenet"
# There are versions 1 and 2 of shapenet, we use v1 for the databse, and v2 for the models.
g_shapenet_url = "http://shapenet.cs.stanford.edu/shapenet/obj-zip/ShapeNetCore.v"
g_pickle_file_name = "/shapenet_db2.pickle.bz2"

g_futures_to_release = Queue()
g_num_converters = 0
g_converters = Queue()
g_converter_loops = []
g_converter_threads = []
g_shapenet_db = None


def pickle_file_exists():
    pickle_path = get_local_shape_loc() + g_pickle_file_name
    return os.path.exists(pickle_path)


def get_database():
    global g_shapenet_db
    if g_shapenet_db == None:
        if pickle_file_exists():
            f = bz2.BZ2File(get_local_shape_loc() + g_pickle_file_name, "rb")
            g_shapenet_db = pickle.load(f)
            f.close()
            # Shapenet v1, where the db comes from, has a few extra models that v2 has not converted.
            # TODO make it download shapenet 1 models, normalize them, and put them in.
            # For now we will just remove those.
            del g_shapenet_db["02834778"]
            del g_shapenet_db["02858304"]
        else:
            g_shapenet_db = None
            print("Please use the menu to build that shapenet ID database.")
    return g_shapenet_db


def get_local_shape_loc():
    global g_local_shape_loc
    if g_local_shape_loc == None:

        env_path = os.getenv("SHAPENET_LOCAL_DIR")
        if env_path == None:
            resolved_data_path = carb.tokens.get_tokens_interface().resolve("${data}")
            g_local_shape_loc = resolved_data_path + "/shapenet"
            print(f"env var SHAPENET_LOCAL_DIR not set, using default data dir {g_local_shape_loc}")
        else:
            g_local_shape_loc = env_path
            print(f"Using local env var SHAPENET_LOCAL_DIR {env_path}")

    return g_local_shape_loc
