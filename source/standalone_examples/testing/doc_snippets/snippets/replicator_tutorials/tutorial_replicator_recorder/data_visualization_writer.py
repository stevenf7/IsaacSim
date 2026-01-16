"""Data Visualization Writer

This writer can be used to visualize various annotator data.

Supported annotators:
- bounding_box_2d_tight
- bounding_box_2d_loose
- bounding_box_3d

Supported backgrounds:
- rgb
- normals

Args:
    output_dir (str):
        Output directory for the data visualization files forwarded to the backend writer.
    bounding_box_2d_tight (bool, optional):
        If True, 2D tight bounding boxes will be drawn on the selected background (transparent by default).
        Defaults to False.
    bounding_box_2d_tight_params (dict, optional):
        Parameters for the 2D tight bounding box annotator. Defaults to None.
    bounding_box_2d_loose (bool, optional):
        If True, 2D loose bounding boxes will be drawn on the selected background (transparent by default).
        Defaults to False.
    bounding_box_2d_loose_params (dict, optional):
        Parameters for the 2D loose bounding box annotator. Defaults to None.
    bounding_box_3D (bool, optional):
        If True, 3D bounding boxes will be drawn on the selected background (transparent by default). Defaults to False.
    bounding_box_3d_params (dict, optional):
        Parameters for the 3D bounding box annotator. Defaults to None.
    frame_padding (int, optional):
        Number of digits used for the frame number in the file name. Defaults to 4.

"""
