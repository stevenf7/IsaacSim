from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CUDAExtension

import os

dir_path = os.path.dirname(os.path.realpath(__file__))

setup(
    name="torch_wrap",
    ext_modules=[CUDAExtension("torch_wrap", [os.path.join(dir_path, "torch_wrap/Py_WrapTensor.cpp")])],
    cmdclass={"build_ext": BuildExtension},
)
