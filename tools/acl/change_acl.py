# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os
import sys

bin_path = os.path.dirname(os.path.realpath(__file__))

sys.path.append(f"{bin_path}/../lib")

import nvidia.pyenv.bootstrap.v5_0 as bs

bs.bootstrap(
    runtime_dir="../../_deps_acl",
    pip_requirements_file="pip.requirements.txt",
    packman_project_file="packman-dependencies.xml",
    subdirs={"ovc": "python", "common": "lib"},
)

import argparse
import asyncio
import json
import re
import shutil
import zipfile
from datetime import datetime
from pprint import pprint

from nvidia.sysutils import pop_dir_pos, push_dir_pos

description = "Syncs OV file meta to a directory"


class defaults:
    user = "hmazhar"
    password = "hmazhar"
    concurrent_saves = 10


def check_ret(ret):
    if ret.status != ok_resp:
        print("Omniverse says: " + ret.statusDescription)
        sys.exit(1)
    return ret


def parse_args():
    argparser = argparse.ArgumentParser(description=description)

    argparser.add_argument("server", metavar="server", help="Source server")

    argparser.add_argument(
        "-u", "--user", metavar="user", default=defaults.user, dest="user", help=f"Username (default {defaults.user})"
    )

    argparser.add_argument(
        "-p",
        "--password",
        metavar="password",
        default=defaults.password,
        dest="password",
        help=f"Password (default {defaults.password})",
    )

    global args
    args = argparser.parse_args()


def init():
    parse_args()
    import omni.aioconnection as oc

    global oc

    print("-" * 79)

    global loop
    global conn
    global ok_resp
    global not_found_resp

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(None)

    ok_resp = oc.OmniErrorType.kOmniErrorTypeOk
    not_found_resp = oc.OmniErrorType.kOmniErrorTypeInvalidPath
    settings = oc.OmniConnectionLibrarySettings()
    settings.version = oc.OmniverseConnectionLibraryVersion
    oc.omniInitialize(settings, loop)

    conn = oc.OmniverseConnection(args.server, args.user, args.password, 30)
    check_ret(loop.run_until_complete(conn.authorize()))
    ping = check_ret(loop.run_until_complete(conn.ping()))

    print(f"Connected to {args.server}, version {ping.version}")
    print("-" * 79)


async def main():

    acl_default = {
        "admin": ["read", "write", "admin"],
        "isaac_admin": ["read", "write", "admin"],
        "gm": ["read", "write", "admin"],
        "users": ["read"],
    }
    now = datetime.now()
    print("Timestamp: ", now)
    print("starting acl check (will only print if file is changed)")
    file_list = await conn.list("/Isaac", recursive=1, show_hidden=1)
    for file_meta in file_list:
        acl = await conn.get_acl(file_meta.path)
        check = False
        if all(key in acl.acls for key in ("admin", "isaac_admin", "gm", "users")):
            if acl.acls["admin"] != ["read", "write", "admin"]:
                check = True
            if acl.acls["isaac_admin"] != ["read", "write", "admin"]:
                check = True
            if acl.acls["gm"] != ["read", "write", "admin"]:
                check = True
            if acl.acls["users"] != ["read"]:
                check = True
        else:
            check = True

        if check:
            print("Acl for: ", file_meta.path, " not correct: ", acl.acls, " resetting to: ", acl_default)
            await conn.change_acl(file_meta.path, acl_default)
    await conn.disconnect()
    oc.omniShutdown()
    pass


init()
loop.run_until_complete(main())
loop.close()
