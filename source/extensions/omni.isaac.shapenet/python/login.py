import time
from .globals import *
from .shape import get_links, download_file
import os
import omni.kit.pipapi
import omni.ui as ui

#   "Keep Help text the width of this line or shorter -------------------------------",
ADD_DB_TEXT = (
    "    Please register an account at https://www.shapenet.org/ so you can make the "
    "database of ShapeNetCore.V1 csv files necessary to run this extension.  Once you "
    "have a validate shapenet.org login, use the menu to create the database.  You "
    "should only have to do this once.\n\n"
)

HELP_TEXT = (
    "    This omni.isaac.shapenet plugin allows you to add ShapeNetCore.V2 models from shapenet.org to your stage in Omniverse Kit.\n\n"
    "    You can use the ShapeNet menu to add shapes.\n\n"
    "    You can also use an external python session to send json formatted commands via http and load shapes with comm_kit.py.\n\n"
    "    See comm_kit.test_comm() or run:\n"
    "\t>  jupyter notebook ShapeNet Python Example.ipynb\n"
    "for examples.\n\n"
    "    If you already have ShapeNetCore V2 installed locally, this plugin can use the local files.  Use the env var SHAPENET_LOCAL_DIR to set that location (IMPORTANT NOTE: Make sure there are no periods, ., in the path name), otherwise, omni.isaac.shapenet will use the default ${data}/shapenet folder.  By using local folders, you can edit shapenet models before their conversion to usd.  If you want to keep the original file, just save the modified file as "
    ' "models/modified/model.obj" in that shape\'s /models folder.\n\n'
    "    If the shape is already on the omniverse server at g_omni_shape_loc (defaults to /Projects/shapenet), then that model will be used instead of the downloaded original or locally saved or modified shapenet obj file.\n\n"
)

WIDGET_WIDTH = 130

# this function is used to make sure the user can log into shapenet.org.  It should be used before creating the pickle.
def try_login(username, password):
    import webbot

    b = webbot.Browser()
    b.go_to("shapenet.org/account")
    b.type(username, into="username")
    b.type(password, into="password")
    b.click("Sign in")
    time.sleep(1)
    # if we are logged in we should be able to re-open the page and see congratulations!
    b.refresh()
    time.sleep(1)
    page_source = b.get_page_source()
    login_success = page_source.find("Congratulations!") > -1

    return login_success


# This is the base script to check if the user has a login and gather the CVS files from
# http://shapenet.cs.stanford.edu/shapenet/obj-zip/ShapeNetCore.v1/ to save locally
def save_v1_csvs(username, password, save_path):

    import urllib.request

    if try_login(username, password):
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        url = g_shapenet_url + "1/"
        file_count_zero = 57
        for href in get_links(urllib.request.urlopen(url).read().decode("unicode-escape")):
            if href[-1] == "v" and href[0] == "0":
                print(f"{file_count_zero} --Downloading {href} to {save_path}.")
                file_count_zero = file_count_zero - 1
                download_file(save_path + href, url + href)
        return True
    else:
        print("Please go to shapenet.org and get a valid login.")
        return False


# this helper function creates a synsetDB entry from a shapenet v1 cvs file.
def create_synsetDBEntry(csv_file):
    import csv

    readCSV = csv.reader(csv_file, delimiter=",")
    skipFirst = True
    synsetDb = {}
    for row in readCSV:
        if skipFirst:
            skipFirst = False
            continue
        modelId = row[0]
        modelDb = modelId[: modelId.find(".")]
        modelId = modelId[modelId.find(".") + 1 :]

        wnsynset = row[1]
        wnlemmas = row[2]
        up = row[3]
        front = row[4]
        name = row[5]
        tags = row[6]

        synsetDb[modelId] = (wnsynset, wnlemmas, up, front, name, tags)
    return synsetDb


# This is the script used to create the shapenet_db2.pickle.bz2 file if the user already has shapenet v1 downloaded.
def create_db_from_files(path):
    import glob

    csv_files = glob.glob(path + "/*.csv")

    snDb = {}
    for filename in csv_files:
        synsetId = filename[-12:-4]

        with open(filename, encoding="utf8") as csv_file:
            snDb[synsetId] = create_synsetDBEntry(csv_file)

    return snDb


# save and test the pickled databse.
def save_and_testDB(snDb, out_file):
    # simple sanity check to make sure the input database is valid so we don't write out a crap one.
    if not len(snDb) == 57:
        return False

    import bz2

    try:
        import cPickle as pickle
    except:
        import pickle
    sfile = bz2.BZ2File(out_file, "wb")
    pickle.dump(snDb, sfile)
    sfile.close()
    f = bz2.BZ2File(out_file, "rb")

    new_dict = pickle.load(f)
    f.close()
    if len(new_dict) == 57:
        print("ID Database created successfully!")
        return True
    else:
        print("Failed to create ID Database :(")
        return False


class ShapenetLogin:
    def __init__(self, shapenetMenu, icon_path):
        self._shapenetMenu = shapenetMenu
        self._models = {}
        self.icon_path = icon_path
        self.build_window()

    def build_window(self):
        """ build ShapeNet Login window"""
        self._window = ui.Window(
            title="ShapeNet Loader", width=400, height=150, visible=False, dockPreference=ui.DockPreference.LEFT_BOTTOM
        )
        self._window.deferred_dock_in("Console", omni.ui.DockPolicy.DO_NOTHING)
        with self._window.frame:
            with ui.VStack():
                with ui.HStack(height=20):
                    ui.Label("Username or Email: ", alignment=ui.Alignment.CENTER, width=WIDGET_WIDTH)
                    self._username = ui.StringField()
                    img_url = str(self.icon_path.joinpath("help.png"))
                    ui.Spacer(width=6)
                    self._models["help_button"] = ui.Button(
                        "Help", width=0, clicked_fn=lambda b=None: self._on_help_menu_click()
                    )
                    # ui.Image(img_url, width=20, tooltip="Help")
                ui.Spacer(height=10)
                with ui.HStack(height=20):
                    ui.Label("Password:", alignment=ui.Alignment.CENTER, width=WIDGET_WIDTH)
                    self._password = ui.StringField()
                    self._password.password_mode = True
                ui.Spacer(height=10)
                with ui.HStack(height=20):
                    ui.Button("Sign In to shapenet.org", clicked_fn=lambda b=None: self._on_login_fn(b))

    def _on_help_menu_click(self):
        help_message = ""
        if not pickle_file_exists():
            help_message = ADD_DB_TEXT
        help_message = help_message + HELP_TEXT

        flags = ui.WINDOW_FLAGS_NO_RESIZE | ui.WINDOW_FLAGS_MODAL
        flags |= ui.WINDOW_FLAGS_NO_SCROLLBAR
        self._help_window = ui.Window("Shapenet Help", width=500, height=0, flags=flags)
        with self._help_window.frame:
            with ui.VStack(name="root", style={"VStack::root": {"margin": 10}}, height=0, spacing=20):
                ui.Label(help_message, alignment=ui.Alignment.LEFT, word_wrap=True)

    def _on_login_fn(self, widget):
        csv_location = get_local_shape_loc() + "/v1_csv/"
        logged_in = save_v1_csvs(
            self._username.model.get_value_as_string(), self._password.model.get_value_as_string(), csv_location
        )
        if not logged_in:
            print(f"Attempting to use local files if they already exist in {csv_location}.")
        snDb = create_db_from_files(csv_location)
        if save_and_testDB(snDb, get_local_shape_loc() + g_pickle_file_name):
            self._shapenetMenu._hide_db_show_add()
        self._window.visible = False
