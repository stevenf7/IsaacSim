# Overview

This extension enables a set of UI based examples demonstrating the cuOpt service for routing optimization.  These examples include:

1. Create Network Example : A simple example to create a waypoint network with nodes and edges. This extension provides tools to create networks that can be saved and re-loaded for optimization problems.

2. Cost Matrix Example : A simple example with randomly generated routing problems represented by simple geometry. This extension directly expresses the  optimization problem to be solved as a cost matrix (matrix of pairwise costs of travel between locations).

3. Waypoint Graph Example : This example leverages a waypoint graph to represent the cost of travel within the environment. In addition, this example leverages omni.cuopt.visualization to process and visualize the waypoint graph.

4. Intra-Warehouse Transport Demo :  This example builds upon the Waypoint Graph Example and demonstrates a more complex waypoint graph in the context of an intra-warehouse goods/equipment transport scenario.

## Requirements
To use this extension you must either have access to a running instance of the cuOpt microservice (local or remote) or credentials to the cuOpt managed service. Install [cuOpt](https://github.com/NVIDIA/cuopt/) or experience and access managed service [here](https://build.nvidia.com/nvidia/nvidia-cuopt)


## Recommended Use
This extension demonstrates a small subset of features of the cuOpt service. The code for this extension is made available and should be extended for specific use cases when needed. A complete list of available features can be found in the [cuOpt docs](https://docs.nvidia.com/cuopt/)
