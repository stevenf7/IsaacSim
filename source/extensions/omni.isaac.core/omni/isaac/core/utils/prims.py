from pxr import UsdGeom


def set_usd_visibility(prim, visible: bool):
    """Sets the visibility of the prim in stage. The method does this through the USD API.

    Args:
        visible (bool): flag to set the visibility of the usd prim in stage.
    """
    imageable = UsdGeom.Imageable(prim)
    if visible:
        imageable.MakeVisible()
    else:
        imageable.MakeInvisible()
    return
