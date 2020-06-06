from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CUDAExtension


setup(name="omni_dl_examples", version="0.1dev", packages=["omni_dl_examples"])

setup(
    name="torch_wrap",
    ext_modules=[CUDAExtension("torch_wrap", ["omni_dl_examples/ext/Py_WrapTensor.cpp"])],
    cmdclass={"build_ext": BuildExtension},
)
