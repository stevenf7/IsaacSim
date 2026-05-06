## Features and Specification

This depth sensor should be used with a resolution of 512 x 424 px (0.2 MP) and a maximum frequency of 30 Hz.

In order to obtain the depth values, use e.g. the depth_to_camera annotator described [here](https://docs.omniverse.nvidia.com/py/replicator/latest/source/extensions/omni.replicator.core/docs/API.html#distance-to-camera).

## Visualization of Fields 

In order to visualize the different volumes (fields) in which safety relevant features may be implemented, this model includes 3D models of these 3D volumes.
To switch between different fields, use the Variant Set "Field" defined on the default prim. The meaning of these fields can be found on the [product page](https://www.sick.com/safeVisionary2). The most important information is summarized in the table below:

| Field   | Name           | Opening angle | Range |
|---------|----------------|---------------|-------|
| Field00 | None | - | - |
| Field01 | Protective Field, Hand | 68° × 42° | 1 m |
| Field02 | Protective Field, Arm | 68° × 42° | 1.6 m |
| Field03 | Protective Field, Leg/Body | 68° × 42° | 2 m |
| Field04 | Protective Field, Extended Range | 68° × 42° | 4 m |
| Field05 | Contour Detection Field, Hand | 68° × 58° | 1 m |
| Field06 | Contour Detection Field, Arm | 68° × 58° | 1.6 m |
| Field07 | Contour Detection Field, Leg/Body/Gap 40 cm | 68° × 58° | 2 m |
| Field08 | Contour Detection Field, Extended Range/Gap 100 cm | 68° × 58° | 4 m |
| Field09 | Warning Field | 68° × 58° | 7.37 m |
| Field10 | Field of View: Measurement Data | 68° × 58° | 16 m |


> ℹ️ **Note**  
> For the datasheet and full list of specifications, visit the [safeVisionary2 product page](https://www.sick.com/safeVisionary2).
>
> For guidance on how to use this sensor optimally in Isaac Sim or for information about a higher-fidelity sensor model (including a noise model and the intensity data), use the contact function on the [SICK digital twin landing page](https://www.sick.com/digital-twin).
