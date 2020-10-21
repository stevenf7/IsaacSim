# Deep Learning Examples
This repo contains simple examples of DL applications within Omniverse Kit.

## Requirements
- Anaconda

## Setup
Create and activate the conda environment
```
conda env create -f environment.yml
conda activate isaac-sim
```

install custom torch wrapper
```
python setup.py install
```

### Setup Environment Variables
Use `setenv` script to add Omni Kit libraries to PYTHONPATH and Add CARB_PATH
#### Windows
`setenv.bat`

#### Linux
`source setenv.sh`

## How To Run
See the Isaac Sim documentation for how to run the samples in this folder