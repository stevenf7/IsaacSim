import omni

try:
    from onshape_client import Client
except ImportError:
    print("onshape not found. attempting to install...")
    omni.kit.pipapi.install("onshape_client==1.6.3")
    from onshape_client import Client

from pathlib import Path
import os
import carb

import json

import webbrowser
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer


from threading import Lock

DEFAULT_ONSHAPE_KEY = "/persistent/ext/omni.isaac.onshape_importer/API_KEY"
DEFAULT_ONSHAPE_SECRET = "/persistent/ext/omni.isaac.onshape_importer/API_SECRET"


def set_api_keys(key, secret):
    carb.settings.get_settings().set(DEFAULT_ONSHAPE_KEY, key)
    carb.settings.get_settings().set(DEFAULT_ONSHAPE_SECRET, secret)


class OnshapeAuthServer(BaseHTTPRequestHandler):
    code = None
    state = None

    def do_GET(self):
        try:
            parsed_url = urlparse(self.path)
            OnshapeAuthServer.params = self.path.split(" ")[-1]
            qs = parse_qs(parsed_url.query)
            if "code" in qs:
                OnshapeAuthServer.code = qs["code"][0]
            if "state" in qs:
                OnshapeAuthServer.state = qs["state"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>Onshape Importer: Succes</title></head>", "utf-8"))
            self.wfile.write(bytes("<body>", "utf-8"))
            self.wfile.write(
                bytes(
                    "<p>You have successfully authorized access to your Onshape account. <br>You can continue to work in your application.</p>",
                    "utf-8",
                )
            )
            self.wfile.write(bytes("</body></html>", "utf-8"))
        except Exception as e:
            carb.log_error("Error handling auth callback GET: " + str(e))

    def log_message(self, format, *args):
        return


class OnshapeClient(object):
    __onshape_client = None
    __user_mats_lib = None
    __lock = Lock()

    @staticmethod
    def get_oauth_client():
        hostName = "localhost"
        serverPort = 4518
        client_id = "7XVZWE3MDZOCYSXEXUJLN4LNHADB42ASGPUPV6Y="
        client_secret = "QZIMKKPIZYQO473R72QEU333XY33NSOXSOMMRUOJQ7HEHRDSPMBA===="

        def auth_callback(url, fetch_token):
            try:
                qs = parse_qs(urlparse(url).query)
                state = None
                if "state" in qs:
                    state = qs["state"][0]
                webServer = HTTPServer((hostName, serverPort), OnshapeAuthServer)

                # Credentials you get from registering a new application

                webbrowser.get().open(url)

                try:
                    webServer.handle_request()
                except KeyboardInterrupt:
                    pass
                # thread = threading.Thread(target=webServer.handle_request)
                # thread.run()
                if state == OnshapeAuthServer.state:
                    code = OnshapeAuthServer.code
                webServer.server_close()
                response_uri = "https://{}:{}/oauth-redirect{}".format(
                    hostName, serverPort, OnshapeAuthServer.params[1:]
                )
                # print(response_uri)
                Client.get_client().set_grant_authorization_url_response(response_uri)
                # fetch_token()
            except Exception as e:
                carb.log_error("error attempting to open Onshape Authentication: " + str(e))

        OnshapeClient.__onshape_client = Client(
            keys_file=None,
            open_authorize_grant_callback=auth_callback,
            configuration={
                "client_id": client_id,
                "client_secret": client_secret,
                "oauth_authorization_method": "python_callback",
            },
        )

    @staticmethod
    def get():
        with OnshapeClient.__lock:
            if not OnshapeClient.__onshape_client:
                if Client.singleton_instance:
                    OnshapeClient.__onshape_client = Client.get_client()
                else:
                    api_key = carb.settings.get_settings().get(DEFAULT_ONSHAPE_KEY)
                    api_secret = carb.settings.get_settings().get(DEFAULT_ONSHAPE_SECRET)
                    if api_key and api_secret:
                        OnshapeClient.__onshape_client = Client(
                            keys_file=None, configuration={"access_key": api_key, "secret_key": api_secret}
                        )
                    else:
                        OnshapeClient.get_oauth_client()

                    # Override the API accept map to workaround the API bug
                    OnshapeClient.__onshape_client.assemblies_api.get_features.headers_map["accept"] = [
                        "application/vnd.onshape.v1+json;charset=UTF-8;qs=0.1"
                    ]
            return OnshapeClient.__onshape_client.get_client()

    @staticmethod
    def get_material_library(did, eid):
        url = "https://cad.onshape.com/api/materials/libraries/d/{}/e/{}".format(did, eid)
        r = OnshapeClient.get().api_client.request("GET", url, _preload_content=False, query_params={})
        if r.status == 200:
            return json.loads(r.data)
        return False

    @staticmethod
    def get_default_material_library():
        return OnshapeClient.get_material_library("2718281828459eacfeeda11f", "6bbab304a1f64e7d640a2d7d")

    @staticmethod
    def get_default_material_libraries(update=False):
        if update or not OnshapeClient.__user_mats_lib:
            user_settings = OnshapeClient.get().users_api.get_user_settings_current_logged_in_user()
            libraries = user_settings["material_library_settings"]
            OnshapeClient.__user_mats_lib = [
                OnshapeClient.get_material_library(l["document_id"], l["element_id"])
                for l in libraries["libraries"] + libraries["company_libraries"]
            ]
        return OnshapeClient.__user_mats_lib

    @staticmethod
    def update_metadata(did, wdid, wid, eid, pid, body):
        url = "https://cad.onshape.com/api/metadata/d/{}/{}/{}/e/{}/p/{}".format(did, wdid, wid, eid, pid)
        headers = {
            "accept": "application/vnd.onshape.v1+json;charset=UTF-8;qs=0.1",
            "Content-Type": "application/json;charset=UTF-8; qs=0.09",
            "content-length": str(len(body)),
        }
        r = OnshapeClient.get().api_client.request(
            method="POST", url=url, body=json.loads(body), headers=headers, _preload_content=False, query_params={}
        )
        return r
