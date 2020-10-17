from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CUDAExtension


setup(
    name="torch_wrap",
    ext_modules=[CUDAExtension("torch_wrap", ["torch_wrap/Py_WrapTensor.cpp"])],
    cmdclass={"build_ext": BuildExtension},
)
