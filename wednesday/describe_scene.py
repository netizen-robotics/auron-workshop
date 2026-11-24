"""Describe a saved RGB frame with Gemma 4. This script has no ROS connection."""

import argparse

from gemma import MODEL, describe


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--model", default=MODEL)
    args = parser.parse_args()
    try:
        print(describe(args.image, args.model))
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"{error}\n")
