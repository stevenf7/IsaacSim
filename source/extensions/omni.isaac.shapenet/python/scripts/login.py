import carb
import carb.settings
from omni.kit.settings import create_setting_widget, create_setting_widget_combo, SettingType
import omni.kit.ui
import omni.kit.commands
import time
from pxr import Gf
from collections import OrderedDict
from .globals import *
from .shape import get_links, download_file
import random
import os
from omni import ui

EXTENSION_NAME = "Create Shapenet ID Database"
EXTENSION_DESC = "Create Shapenet ID Database"
WIDGET_WIDTH = 130

# this function is used to make sure the user can log into shapenet.org.  It should be used before creating the pickle.
def try_login(username, password):
    omni.kit.pipapi.install("webbot")
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
    def get_name(self):
        return EXTENSION_NAME

    def get_description(self):
        return EXTENSION_DESC

    def __init__(self, shapenetMenu):
        self._shapenetMenu = shapenetMenu
        self._settings = carb.settings.get_settings()

        self.build_window()

    def build_window(self):
        """ build ShapeNet Login window"""
        self._window = ui.Window("ShapeNet Login", width=400, height=150)
        with self._window.frame:
            with ui.VStack():
                with ui.HStack(height=20):
                    ui.Label("Username or Email: ", alignment=ui.Alignment.CENTER, width=WIDGET_WIDTH)
                    self._username = ui.StringField()
                ui.Spacer(height=10)
                with ui.HStack(height=20):
                    ui.Label("Password:", alignment=ui.Alignment.CENTER, width=WIDGET_WIDTH)
                    self._password = ui.StringField()
                    self._password.password_mode = True
                ui.Spacer(height=10)
                with ui.HStack(height=20):
                    ui.Button("Sign In to shapenet.org", clicked_fn=lambda b=None: self._on_login_fn(b))

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
