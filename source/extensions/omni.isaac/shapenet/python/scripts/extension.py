""" This plugin is used to load shapenet objects into Kit.

        If the shape already exists as a USD on a connected omniverse server, then
    it will use that version, unless there is an override.
        If not on omniverse, the plugin will convert the obj from a folder on the
    machine--fetching to the local machine from the web if needed--and upoad it to
    omniverse if there is a connection.
"""

from omni.assetimport import assetconverter

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import threading
from time import sleep, time

from .comm import process_request_in_thread
from .exceptions import ShapenetException
from .globals import *
from .menu import ShapenetMenu

from queue import Queue

DEBUG_PRINT_ON = False

# The listener thread will fill these so that main thread can consume them.
g_requests = Queue()
# The The listener, will respond
g_responses = Queue()


class ShapeNetRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Set-Cookie", "foo=bar")
        self.end_headers()
        self.wfile.write(
            json.dumps(
                {
                    "success": False,
                    "received": "ok",
                    "message": "This Is a Long Drive for Someone with Nothing to Think About",
                }
            )
        )

    def do_POST(self):
        # This recieves the outside posted data, which makes a request to the system.
        request_start = time()
        length = int(self.headers["Content-Length"])
        request = json.loads(self.rfile.read(length))
        g_requests.put(request)
        # wait for the response, and send when you get it.
        while g_responses.empty():
            # print("waiting for response...")
            sleep(0.1)
        if DEBUG_PRINT_ON:
            print("AFTER THE POSSIBLE EXCEP")
        response = g_responses.get()
        response["time"] = time() - request_start

        self.send_response_only(200)
        self.send_header("Set-Cookie", "foo=bar")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode(encoding="utf_8"))

    do_PUT = do_POST
    do_DELETE = do_GET


def run_server(httpd):
    print(f"FYI, omni.isaac.shapenet's receiver for external messages has started. on {g_bind_address}")
    httpd.serve_forever()


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._menu = ShapenetMenu()
        self._editor = omni.kit.editor.get_editor_interface()
        # Creat the TCPServer and run it in another thread, but keep handle to it so
        # we can call shutdown loater.
        server_address = (g_bind_address[0], int(g_bind_address[1]))
        self._http_server = HTTPServer(server_address, ShapeNetRequestHandler)
        self.thread = threading.Thread(target=run_server, args=(self._http_server,))
        # get an event loop for each thread that we are going to run converters in.
        for x in range(g_num_converters):
            new_loop = asyncio.new_event_loop()
            t = Thread(target=start_loop, args=(new_loop,))
            g_converter_loops.append(new_loop)
            g_converter_threds.append(t)

        self.sub = self._editor.subscribe_to_update_events(self._on_update)
        self.thread.start()
        for x in range(g_num_converters):
            g_converters.put(x)
            g_converter_threads[x].start()

    def on_shutdown(self):
        if DEBUG_PRINT_ON:
            print("Enter on_shutdown")
        self._http_server.shutdown()
        if DEBUG_PRINT_ON:
            print("After self._http_server.shutdown() in on_shutdown")
        self.thread.join()
        if DEBUG_PRINT_ON:
            print("After self.thread.join() in on_shutdown")

        for x in range(g_num_converters):
            g_converter_loops[x].stop()
            g_converter_loops[x].close()
            g_converter_threads[x].join()

        self._menu.shutdown()
        if DEBUG_PRINT_ON:
            print("After self._menu.shutdown() in on_shutdown")
        self._menu = None
        if DEBUG_PRINT_ON:
            print("After self._menu = None in on_shutdown")

    def _on_update(self, dt):
        while not g_futures_to_release.empty():
            future = g_futures_to_release.get()
            assetconverter.omniConverterReleaseFuture(future)

        if not g_requests.empty():
            request = g_requests.get()
            if DEBUG_PRINT_ON:
                print("Call process_request_in_thread with request: ", request)
            process_request_in_thread("new", g_responses, self._menu, request)
