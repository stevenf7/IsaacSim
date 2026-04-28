# -- Test setup --
import omni.usd
from pxr import Sdf, Usd

stage = omni.usd.get_context().get_stage()


def do_something():
    pass


# Create the layer file the snippet expects
Sdf.Layer.CreateNew("my_layer.usd")
# -- End test setup --
from pxr import Sdf

# Get References to all layers
root_layer = stage.GetRootLayer()
session_layer = stage.GetSessionLayer()

# Add a SubLayer to the Root Layer
additional_layer = layer = Sdf.Layer.FindOrOpen("my_layer.usd")
root_layer.subLayerPaths.append(additional_layer.identifier)

# Set Edit Layer
# Method 1
with Usd.EditContext(stage, root_layer):
    do_something()

# Method 2
stage.SetEditTarget(additional_layer)


# Make non-persistent changes to the stage (won't be saved regardless if you call stage.Save)

with Usd.EditContext(stage, session_layer):
    do_something()
