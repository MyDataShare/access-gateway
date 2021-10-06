import os
import base64
import json
from pathlib import Path


class EnvironmentReferenceError(Exception):
    pass


def decode_base64(input_str: str) -> str:
    base64_bytes = input_str.encode("utf-8")
    message_bytes = base64.b64decode(base64_bytes)
    return message_bytes.decode("utf-8")


def read_json(directory: Path, filename: str):
    with open(directory.joinpath(filename)) as f:
        return json.load(f)


def walk_dir(directory: str, callback, ending_with=None):
    for subdir, dirs, files in os.walk(directory):
        for filename in files:
            filepath = subdir + os.sep + filename

            if ending_with and not filepath.endswith(ending_with):
                continue

            callback(filepath, filename)
