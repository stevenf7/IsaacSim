import numpy as np

## import data from file
sensor_pattern = np.loadtxt("filename.csv", delimiter=",")
batch_size = np.shape(sensor_pattern)[0]
sensor_pattern = np.deg2rad(sensor_pattern).T.copy()  ##  MUST USE .copy()
