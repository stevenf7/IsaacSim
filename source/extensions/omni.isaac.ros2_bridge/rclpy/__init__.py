import os, sys
import omni.ext


class Extension(omni.ext.IExt):
    def on_startup(self):
        sys.path.append(os.path.join(os.path.dirname(__file__)))

    def on_shutdown(self):
        sys.path.remove(os.path.join(os.path.dirname(__file__)))
