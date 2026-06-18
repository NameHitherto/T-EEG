"""Entry point: ``python -m seed-v`` prints the SEED-V dataset summary."""

from .inspect import print_dataset_info

if __name__ == "__main__":
    print_dataset_info()
