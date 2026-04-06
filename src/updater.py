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
import hashlib
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

# REMEMBER TO UPDATE THIS EACH RELEASE
VERSION = "1.0.1"

REPO = "Urban-Elf/LentBuddy"

# ----------------------------
# Public key for signature verification (hex)
# ----------------------------
PUBLIC_KEY_HEX = "a5da168851cb907bba8c5a54aac8a448626ebc57989066e022a3e0966c8f6a25"

# Safety check for frozen state (PyInstaller) so dev environment doesn't try to apply updates
NOT_FROZEN = not getattr(sys, 'frozen', False)

# ----------------------------
# Version helpers
# ----------------------------
def normalize_version(tag: str) -> str:
    return tag.lstrip("v").strip()

def get_latest_release():
    url = f"https://api.github.com/repos/{REPO}/releases/latest"
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())

# ----------------------------
# Platform detection
# ----------------------------
def get_platform_asset():
    system = platform.system().lower()
    if system == "windows":
        return "lentbuddy-windows.zip", "lentbuddy.exe"
    elif system == "darwin":
        return "lentbuddy-macos.zip", "lentbuddy"
    else:
        return "lentbuddy-linux.zip", "lentbuddy"

# ----------------------------
# apply pending update
# ----------------------------
def run_updater():
    import sys
    import os

    _, _, pid, current_exe, new_exe = sys.argv

    pid = int(pid)

    print(f"Updater started. Waiting for PID {pid} to exit...")

    # Wait for main process to exit
    while True:
        try:
            os.kill(pid, 0)
            time.sleep(0.5)
        except OSError:
            break  # process is gone

    print("Main process exited. Applying update...")

    # Retry replace (Windows can lag a bit)
    for _ in range(10):
        try:
            os.replace(new_exe, current_exe)
            break
        except PermissionError:
            time.sleep(0.5)
    else:
        print("Failed to replace executable.")
        return

    print("Update applied.")

def get_current_executable():
    # If running in dev / script mode
    path = shutil.which(sys.argv[0])
    if path:
        return os.path.realpath(path)
    else:
        # fallback to argv[0] absolute
        return os.path.realpath(sys.argv[0])

# ----------------------------
# Download with progress bar
# ----------------------------
def download_with_progress(urls, dest_paths):
    for url, dest_path in zip(urls, dest_paths):
        with urllib.request.urlopen(url) as response:
            total = int(response.getheader('Content-Length', 0))
            downloaded = 0
            chunk_size = 8192
            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        done = int(50 * downloaded / total)
                        percent = int(100 * downloaded / total)
                        bar = '[' + '=' * done + ' ' * (50 - done) + f'] {percent}%'
                        print(f'\rDownloading update... {bar}', end='', flush=True)
            print()  # for new line after download

# ----------------------------
# Verify signature
# ----------------------------
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

# ----------------------------
# Self-update logic
# ----------------------------
def self_update() -> bool:
    if NOT_FROZEN:
        print("Running in project mode, skipping update check.")
        return False

    print("Checking for updates...")
    try:
        data = get_latest_release()
    except Exception as e:
        print(f"Failed to check for updates: {e}")
        return False

    latest_version = normalize_version(data.get("tag_name", ""))
    if not latest_version:
        print("Could not determine latest version.")
        return False
    if latest_version == VERSION:
        print(f"Already up to date (v{VERSION})")
        return False

    print(f"⬆️ Updating from v{VERSION} → v{latest_version}")

    zip_name, binary_name = get_platform_asset()
    sig_name = zip_name + ".sig"

    asset_url = sig_url = None
    for asset in data.get("assets", []):
        if asset.get("name") == zip_name:
            asset_url = asset.get("browser_download_url")
        elif asset.get("name") == sig_name:
            sig_url = asset.get("browser_download_url")

    if not asset_url or not sig_url:
        print("No compatible update or signature found for your platform.")
        return False

    try:
        tmpdir = tempfile.mkdtemp()

        zip_path = os.path.join(tmpdir, zip_name)
        sig_path = os.path.join(tmpdir, sig_name)

        # Download both the zip and the signature
        download_with_progress([asset_url, sig_url], [zip_path, sig_path])

        # Verify signature
        if not verify_signature(zip_path, sig_path):
            print("Signature verification failed! Update aborted.")
            return False
        print("Signature is valid.")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)
            # Print the extracted files for debugging
            #print("Extracted files:", os.listdir(tmpdir))

        # Downloaded binary
        new_binary = os.path.join(tmpdir, "lentbuddy", binary_name)

        if not os.path.exists(new_binary):
            print(f"Error: {new_binary} does not exist (missing from update).")
            return False

        current_binary = get_current_executable()
        print(f"Current binary: {current_binary}")
        print("Installing update...")
        new_binary_tmp = current_binary + ".new"
        print("Copying from {} to {}".format(new_binary, new_binary_tmp))
        # Stage the new binary by copying it to a temporary location next to the current binary
        shutil.copy2(new_binary, new_binary_tmp)
        # Set executable permissions on the new binary before copying (important for Unix)
        if platform.system() != "Windows":
            os.chmod(new_binary_tmp, 0o755)

        subprocess.Popen([
            current_binary,
            "--apply-update",
            str(os.getpid()),
            current_binary,
            new_binary_tmp
        ])
        
        print("Exiting for update...")
        sys.exit(0)

        return True

    except Exception as e:
        print(f"Update failed: {e}")

    return False
