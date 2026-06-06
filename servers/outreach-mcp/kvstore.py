"""Tiny JSON file store — the only persistence the kept tools need (Hunter credit
balance, LinkedIn daily counters). State, learnings, and profiles are plain files
the model edits directly; this is just for the couple of counters code must own.
Atomic writes (temp + rename) so a crash mid-write can't corrupt the file."""
import json
import os
import tempfile

DEFAULT_DIR = os.path.expanduser("~/.config/job-hunter")


def _dir():
    d = os.environ.get("DATA_DIR") or DEFAULT_DIR
    os.makedirs(d, exist_ok=True)
    return d


def _path(name):
    return os.path.join(_dir(), name)


def load(name):
    """Return the dict at `name`, or {} if the file is missing/empty."""
    try:
        with open(_path(name)) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save(name, data):
    """Atomically write `data` (a dict) to `name`."""
    path = _path(name)
    fd, tmp = tempfile.mkstemp(dir=_dir(), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
