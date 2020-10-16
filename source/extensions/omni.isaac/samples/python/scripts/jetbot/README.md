# Deep Learning Examples
This repo contains simple examples of DL applications within Omniverse Kit.

## Requirements
- Python 3.6 environment (conda works well)
- [Pytorch](https://pytorch.org/) == 1.4
- torchvision == 0.5.0
- Matplotlib >= 3.1.3 (for visualizations)
- requests == 2.23.0 (for the ShapeNet extension)
- six == 1.12.0

## Setup
- `cd to _build/linux-x86_64/release/exts/omni.isaac.samples/omni/isaac/samples/scripts/jetbot``
- `conda env create -f environment.yml  --name isaac-sim`
- `conda activate isaac-sim`
- `cd ../syntheticdata`
- `python setup.py install
Then return back to jetbot
- `cd ../jetbot`
and run
- Environment Variables in setenv.sh 
  - `source setenv.sh`

## Usage
To train a jetbot agent just 
-  `python jetbot_train.py` 
from `_build/linux-x86_64/release/exts/omni.isaac.samples/omni/isaac/samples/scripts/jetbot`