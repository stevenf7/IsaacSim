import os
import sys

# The FlatBuffers-generated files in isaac/ use bare "from isaac.xxx import Xxx" imports.
# Add this directory to sys.path so those relative imports resolve correctly.
_this_dir = os.path.dirname(__file__)
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)
