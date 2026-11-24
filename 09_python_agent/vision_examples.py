"""Use Gemma 4 to compare camera frames or give advisory feedback."""

from importlib import import_module
import argparse

# Both prompts use Ollama vision without ROS access: https://docs.ollama.com/capabilities/vision
gemma = import_module("08_gemma_ollama.gemma")

COMPARE = (
    "The first image is BEFORE and the second image is AFTER. From the camera images alone, "
    "state what visibly changed and what stayed the same. If there is no clear difference, "
    "say so. Do not infer that the robot moved or estimate how far. Answer in three short sentences."
)
ADVISE = (
    "This is one forward-facing RGB frame from a stationary classroom robot. Would you "
    "suggest proposing a short straight move for human review, or waiting for more "
    "information? State your recommendation, visible evidence, and what the single image "
    "cannot establish, including the space beyond the frame. Treat uncertain clearance "
    "as a reason to wait. Do not issue instructions to the robot. Keep the answer brief."
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=gemma.MODEL)
    example = parser.add_subparsers(dest="example", required=True)
    compare = example.add_parser("compare", help="Compare frames in before/after order")
    compare.add_argument("before")
    compare.add_argument("after")
    example.add_parser("advise", help="Get an advisory interpretation of one frame").add_argument("frame")
    args = parser.parse_args()
    try:
        if args.example == "compare":
            result = gemma.ask_about_images([args.before, args.after], COMPARE, args.model)
        else:
            result = gemma.ask_about_images([args.frame], ADVISE, args.model)
        print(result)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
