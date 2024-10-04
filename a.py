import torch

# Print PyTorch version
print("PyTorch version:", torch.__version__)

# Check if CUDA is available and print CUDA version
cuda_available = torch.cuda.is_available()
print("CUDA available:", cuda_available)
if cuda_available:
    print("CUDA version:", torch.version.cuda)

# Test PyTorch with a random tensor
tensor = torch.rand(3, 3)
print("Random Tensor:\n", tensor)
