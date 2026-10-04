"""
Puts everything the desktop app ships next to its .exe into src-tauri/resources:

  resources/python/   Python's official embeddable distribution, unchanged
  resources/app/      the Advertiser itself: start.py and the advertiser package

Why the embeddable distribution and not a one-file bundler: the app's whole pitch is
that it can be inspected. A bundler packs everything into one opaque executable that
antivirus heuristics like to flag; this keeps every file readable in the install
folder, and Python is the one python.org publishes, byte for byte.

The download is checked against a pinned SHA-256. A mismatch stops the build rather
than shipping a runtime nobody can vouch for.

Run from the repository root or from desktop/:   python desktop/scripts/prepare_runtime.py
"""

from __future__ import annotations

import hashlib
import io
import os
import shutil
import sys
import urllib.request
import zipfile

PYTHON_VERSION = "3.12.10"
PYTHON_URL = (f"https://www.python.org/ftp/python/{PYTHON_VERSION}/"
              f"python-{PYTHON_VERSION}-embed-amd64.zip")
# Pinned on first download (2026-10-04). Change it only together with the version.
PYTHON_SHA256 = "4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3"

HERE = os.path.dirname(os.path.abspath(__file__))
DESKTOP = os.path.dirname(HERE)
REPO = os.path.dirname(DESKTOP)
RESOURCES = os.path.join(DESKTOP, "src-tauri", "resources")
CACHE = os.path.join(DESKTOP, ".cache")


def fetch_python() -> bytes:
    os.makedirs(CACHE, exist_ok=True)
    cached = os.path.join(CACHE, os.path.basename(PYTHON_URL))
    if os.path.exists(cached):
        with open(cached, "rb") as handle:
            data = handle.read()
    else:
        print(f"downloading {PYTHON_URL}")
        request = urllib.request.Request(PYTHON_URL, headers={"User-Agent": "MutexxAdvertiser-build"})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
        with open(cached, "wb") as handle:
            handle.write(data)
    digest = hashlib.sha256(data).hexdigest()
    # The pin was taken from a download whose python.exe carries a valid Python
    # Software Foundation Authenticode signature (checked 2026-10-04).
    if digest != PYTHON_SHA256:
        os.remove(cached)
        sys.exit(f"SHA-256 mismatch for {PYTHON_URL}: got {digest}, expected {PYTHON_SHA256}")
    return data


def copy_app(target: str) -> None:
    def ignore(_folder, names):
        return [name for name in names if name in ("__pycache__",) or name.endswith(".pyc")]

    shutil.copytree(os.path.join(REPO, "advertiser"), os.path.join(target, "advertiser"),
                    ignore=ignore)
    shutil.copy2(os.path.join(REPO, "start.py"), target)
    for extra in ("README.md", "CHANGELOG.md"):
        if os.path.exists(os.path.join(REPO, extra)):
            shutil.copy2(os.path.join(REPO, extra), target)


def remove_tree(path: str) -> None:
    """rmtree that survives a brief lock. Inside OneDrive the sync client holds
    freshly written folders for a moment, and Windows answers "access denied"
    until it lets go."""
    import stat
    import time

    def retry(function, target, _info):
        os.chmod(target, stat.S_IWRITE)
        for _ in range(20):
            try:
                function(target)
                return
            except OSError:
                time.sleep(0.25)
        function(target)

    for _ in range(3):
        if not os.path.isdir(path):
            return
        try:
            shutil.rmtree(path, onexc=retry)
        except OSError:
            time.sleep(1)
    if os.path.isdir(path):
        shutil.rmtree(path, onexc=retry)


def main() -> None:
    remove_tree(RESOURCES)
    python_dir = os.path.join(RESOURCES, "python")
    app_dir = os.path.join(RESOURCES, "app")
    os.makedirs(python_dir)
    os.makedirs(app_dir)

    with zipfile.ZipFile(io.BytesIO(fetch_python())) as archive:
        archive.extractall(python_dir)
    copy_app(app_dir)

    files = sum(len(names) for _root, _dirs, names in os.walk(RESOURCES))
    size = sum(os.path.getsize(os.path.join(root, name))
               for root, _dirs, names in os.walk(RESOURCES) for name in names)
    print(f"resources ready: {files} files, {size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
