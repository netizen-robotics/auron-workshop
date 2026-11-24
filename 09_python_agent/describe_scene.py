"""Describe a saved RGB frame with Gemma 4. This script has no ROS connection."""

from importlib import import_module
import argparse

# This CLI gives Gemma an image and prompt. It does not expose ROS tools.
gemma = import_module("08_gemma_ollama.gemma")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--model", default=gemma.MODEL)
    args = parser.parse_args()
    try:
        print(gemma.describe(args.image, args.model))
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"{error}\n")
