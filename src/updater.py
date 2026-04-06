import os
import subprocess
import sys
import platform
import tempfile
import time
import urllib.request
import json
import shutil
import zipfile
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

LOCKFILE = os.path.join(tempfile.gettempdir(), "lentbuddy_update.lock")
VERSION = "1.0.1"
REPO = "Urban-Elf/LentBuddy"
PUBLIC_KEY_HEX = "a5da168851cb907bba8c5a54aac8a448626ebc57989066e022a3e0966c8f6a25"
NOT_FROZEN = not getattr(sys, 'frozen', False)

def get_current_executable():
    return sys.executable if getattr(sys, "frozen", False) else os.path.realpath(sys.argv[0])

# -------------------
# Updater subprocess
# -------------------
def run_updater():
    _, _, current_exe, new_exe = sys.argv

    print("Updater started. Waiting for main app to exit...")

    # Wait until lockfile is removed
    while os.path.exists(LOCKFILE):
        time.sleep(0.5)

    print("Main process exited. Applying update...")

    # Retry replacement (Windows can lock files briefly)
    for _ in range(10):
        try:
            os.replace(new_exe, current_exe)
            break
        except PermissionError:
            time.sleep(0.5)
    else:
        print("Failed to replace executable.")
        return

    if platform.system() != "Windows":
        os.chmod(current_exe, 0o755)

    print("Update applied. Restarting app...")
    subprocess.Popen([current_exe], close_fds=True,
                     creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)

# -------------------
# Download + verify
# -------------------
def get_latest_release():
    url = f"https://api.github.com/repos/{REPO}/releases/latest"
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())

def normalize_version(tag: str) -> str:
    return tag.lstrip("v").strip()

def download_with_progress(urls, dest_paths):
    for url, dest_path in zip(urls, dest_paths):
        with urllib.request.urlopen(url) as response:
            total = int(response.getheader('Content-Length', 0))
            downloaded = 0
            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        done = int(50 * downloaded / total)
                        percent = int(100 * downloaded / total)
                        bar = '[' + '='*done + ' '*(50-done) + f'] {percent}%'
                        print(f'\rDownloading update... {bar}', end='', flush=True)
            print()

def verify_signature(file_path, sig_path):
    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY_HEX))
    with open(file_path, 'rb') as f:
        data = f.read()
    with open(sig_path, 'rb') as f:
        sig = f.read()
    try:
        verify_key.verify(data, sig)
        return True
    except BadSignatureError:
        return False

# -------------------
# Self-update
# -------------------
def self_update() -> bool:
    if NOT_FROZEN:
        print("Running in project mode, skipping update check.")
        return False

    print("Checking for app updates...")
    try:
        data = get_latest_release()
    except Exception as e:
        print(f"Failed to check for updates: {e}")
        return False

    latest_version = normalize_version(data.get("tag_name", ""))
    if latest_version == VERSION or not latest_version:
        print(f"Already up to date (v{VERSION})")
        return False

    print(f"Update available: v{latest_version} (current: v{VERSION})")
    choice = input("Do you want to update now? [Y/n] ").strip().lower()
    if choice not in ('y', 'yes', ''):
        print("Cancelled.")
        return False

    zip_name, binary_name = ("lentbuddy-windows.zip", "lentbuddy.exe") if platform.system().lower() == "windows" else ("lentbuddy-linux.zip", "lentbuddy")
    sig_name = zip_name + ".sig"

    asset_url = sig_url = None
    for asset in data.get("assets", []):
        if asset.get("name") == zip_name:
            asset_url = asset.get("browser_download_url")
        elif asset.get("name") == sig_name:
            sig_url = asset.get("browser_download_url")

    if not asset_url or not sig_url:
        print("No compatible update found.")
        return False

    try:
        tmpdir = tempfile.mkdtemp()
        zip_path = os.path.join(tmpdir, zip_name)
        sig_path = os.path.join(tmpdir, sig_name)

        download_with_progress([asset_url, sig_url], [zip_path, sig_path])

        if not verify_signature(zip_path, sig_path):
            print("Signature verification failed.")
            return False

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        new_binary = os.path.join(tmpdir, "lentbuddy", binary_name)
        if not os.path.exists(new_binary):
            print("Update binary missing.")
            return False

        current_binary = get_current_executable()
        staged_binary = current_binary + ".new"
        shutil.copy2(new_binary, staged_binary)

        # Launch updater subprocess using lockfile
        subprocess.Popen([
            current_binary,
            "--apply-update",
            current_binary,
            staged_binary
        ],
        close_fds=True,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)

        print("Exiting for update...")
        sys.exit(0)

    except Exception as e:
        print(f"Update failed: {e}")
        return False