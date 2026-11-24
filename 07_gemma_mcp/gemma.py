"""Call the local Ollama chat API."""

import base64
import json
from pathlib import Path
# Python sends HTTP JSON directly to the Ollama chat API: https://docs.ollama.com/api/chat
from urllib.request import Request, urlopen

MODEL = "gemma4:e2b"


def ask(messages, *, model=MODEL, tools=None):
    body = {"model": model, "messages": messages, "stream": False,
            "options": {"temperature": 0}}
    # The model proposes tool calls in its reply. This HTTP client only sends tool descriptions.
    if tools:
        body["tools"] = tools
    request = Request("http://127.0.0.1:11434/api/chat",
                      json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urlopen(request, timeout=180) as response:
        return json.load(response)["message"]


def ask_about_images(paths, prompt, model=MODEL):
    # The REST API takes base64 image strings in the order supplied in the prompt.
    return ask([{
        "role": "user",
        "content": prompt,
        "images": [base64.b64encode(Path(path).read_bytes()).decode("ascii") for path in paths],
    }], model=model)["content"]


def describe(path, model=MODEL):
    return ask_about_images([path], (
        "Describe objects actually visible in this Auron RGB image and where they appear in the "
        "frame. Say what is uncertain. Do not guess distances or suggest movements."
    ), model)
