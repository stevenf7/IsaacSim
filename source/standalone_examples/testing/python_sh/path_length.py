import os

# test to give us a heads up if the PATH variable gets too long, can be an issue on windows
print(len(os.environ["PATH"]))
assert len(os.environ["PATH"]) < 2000
