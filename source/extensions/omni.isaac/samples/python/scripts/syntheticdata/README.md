# Deep Learning Examples
This repo contains simple examples of DL applications within Omniverse Kit.

## Requirements
- Python 3.6 environment (conda works well)
- [Pytorch](https://pytorch.org/) == 1.4
- Matplotlib >= 3.1.3 (for visualizations)
- requests == 2.23.0 (for the ShapeNet extension)

## Setup
```
python setup.py install
```

### Setup Environment Variables
Use `setenv` script to add Omni Kit libraries to PYTHONPATH and Add CARB_PATH
#### Windows
`setenv.bat`

#### Linux
`source setenv.sh`

## Examples
### Demo
A simple demo demonstrating how to setup a scene, gather groundtruth and visualize it.
```
python omni_dl_examples/syntheticdata_demo/demo.py
```

## ShapeNet Examples
Before running these examples, you will need to download ShapeNet data from shapenet.org, or through the Isaac Shapenet extension. Once the data is available, update the `SHAPENET_LOCAL_DIR` environment variable to point to the dataset.

### Asset Conversion
The ShapeNet assets can now be converted to USD. We will convert only the geometry to allow for quick loading of assets into our scene.
With the `SHAPENET_LOCAL_DIR` variable set, run the following script. Note, this will create a new directory at {SHAPENET_LOCAL_DIR}_nomat where the geometry-only USD files will be stored.

Example Useage:
```bash
python omni_dl_examples/helpers/shapenet.py --categories chair plane watercraft --max-models 100
```


### Instance Segmentation
Use a PyTorch dataloader together with OmniKit to generate scenes and groundtruth to
train a [Mask-RCNN](https://arxiv.org/abs/1703.06870) model.

Example Useage:
```bash
python omni_dl_examples/segmentation/train.py \
    --root $SHAPENET_LOCAL_DIR'_nomat' \
    --categories chair plane watercraft
```

## Troubleshooting
### Common Issues
- `ModuleNotFoundError: No module named 'carb._carb'`: Ensure that your python environment is version 3.6.