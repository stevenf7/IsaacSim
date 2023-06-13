import scipy

print(scipy.__path__[0])
assert "omni.pip.compute" in scipy.__path__[0]
