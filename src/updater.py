import os
import sys
import platform
import tempfile
import urllib.request
import json
import shutil
import zipfile
import hashlib
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

# REMEMBER TO UPDATE THIS EACH RELEASE
VERSION = "1.0.0"

REPO = "Urban-Elf/LentBuddy"

# ----------------------------
# Public key for signature verification (hex)
# ----------------------------
PUBLIC_KEY_HEX = "a5da168851cb907bba8c5a54aac8a448626ebc57989066e022a3e0966c8f6a25"

# Safety check for frozen state (PyInstaller) so dev environment doesn't try to apply updates
IS_FROZEN = getattr(sys, 'frozen', False)

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
# Windows: apply pending update
# ----------------------------
def apply_pending_update():
    if IS_FROZEN:
        return
    current = os.path.realpath(sys.argv[0])
    new_file = current + ".new"
    if os.path.exists(new_file):
        try:
            os.replace(new_file, current)
            print("Updated to latest version.")
        except Exception:
            pass

# ----------------------------
# Download with progress bar
# ----------------------------
def download_with_progress(url, dest_path):
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
        print()

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
    if IS_FROZEN:
        print("Running in development mode, skipping update check.")
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
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, zip_name)
            sig_path = os.path.join(tmpdir, sig_name)

            # Download files
            download_with_progress(asset_url, zip_path)
            download_with_progress(sig_url, sig_path)

            # Verify signature
            print("Verifying update signature...")
            if not verify_signature(zip_path, sig_path):
                print("Signature verification failed! Update aborted.")
                return False
            print("Signature valid!")

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)

            new_binary = os.path.join(tmpdir, "lentbuddy", binary_name)
            current_binary = os.path.realpath(sys.argv[0])

            print("Installing update...")
            if platform.system().lower() == "windows":
                shutil.copy2(new_binary, current_binary + ".new")
            else:
                shutil.copy2(new_binary, current_binary)
                os.chmod(current_binary, 0o755)
            print("Update complete. Please restart the app (press [Return] to exit).")
            # Wait for return to ensure user sees the message before app exits
            input()
            return True

    except Exception as e:
        print(f"Update failed: {e}")

    return False
