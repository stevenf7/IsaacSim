import torch

print(torch.__path__[0])
assert "omni.pip.torch" in torch.__path__[0]
print(f"Cuda available: {torch.cuda.is_available()}")
assert torch.cuda.is_available()
