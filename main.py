#!/usr/bin/env python3
import sys
import shutil
import subprocess
import requests
import json
import tempfile
from pathlib import Path
import configparser
import re

# Verfity number of inputs
if len(sys.argv) != 2:
    print("Usage: python3 main.py </path/to/gog/file_or_folder>")
    sys.exit(1)

# Capture input from cli
GOG_INPUT = Path(sys.argv[1])

if not GOG_INPUT.is_dir() and not GOG_INPUT.is_file():
    print(f"Error: Input '{GOG_INPUT}' is not a file or directory")
    sys.exit(1)

# Load configuration from ini file
config = configparser.ConfigParser()
config.read('config.ini')

# Get folder paths from config or use default
DEST_DIR = Path(config.get('folders', 'dest_dir', fallback="/DEST"))
TEMP_DIR = Path(config.get('folders', 'temp_dir', fallback="/TEMP"))

# Set directory for processed_files.json file
SCRIPT_DIR = Path(sys.argv[0])
CURRENT_DIR = Path.cwd()
PROCESSED_JSON = Path(CURRENT_DIR, SCRIPT_DIR.parent, "processed_files.json")

# Ensure necessary directories exist
DEST_DIR.mkdir(parents=True, exist_ok=True)

# Regex for locale codes like "xx-xx" (letters only)
LOCALE_CODE = re.compile(r"^[a-z]+-[a-z]+$", re.IGNORECASE)
# Regex for "-locale=xx" style strings
LOCALE_PATTERN = re.compile(r"-locale=[A-Za-z-]+")

# Load processed files list
def load_processed_files():
    if PROCESSED_JSON.exists():
        with open(PROCESSED_JSON, "r") as f:
            return set(json.load(f))
    return set()

# Save processed files list
def save_processed_files(processed_files):
    with open(PROCESSED_JSON, "w") as f:
        json.dump(list(processed_files), f)

processed_files = load_processed_files()

# Fetch metadata from GOG API
def fetch_metadata(game_id):
    api_url = f"https://api.gog.com/products/{game_id}"
    print(f"Fetching metadata for game ID {game_id} from GOG API...")
    response = requests.get(api_url)
    
    if response.status_code != 200:
        print("Error: Unable to fetch data from GOG API.")
        return "Unknown Game", "0000"

    data = response.json()
    gt = data.get("title", "Unknown Game")
    game_title = re.sub(r'[^\w\s]', '', gt)
    release_date = data.get("release_date", "0000")
    if release_date:
        year = release_date.split("-")[0]
    else:
        year = "0000"
    return game_title, year

# Set language and locale as English in goggame.info config file
def set_language(goginfo):
    if isinstance(goginfo, dict):
        print("Fixing dict info...")
        # Fix top-level 'language'
        if "language" in goginfo and goginfo["language"] != "neutral":
            goginfo["language"] = "English"

        # Fix 'languages' arrays
        if "languages" in goginfo and isinstance(goginfo["languages"], list):
            if len(goginfo["languages"]) == 1:
                val = goginfo["languages"][0]
                if isinstance(val, str) and LOCALE_CODE.match(val):
                    goginfo["languages"] = ["en-US"]
        # Recurse into dictionary values
        for k, v in goginfo.items():
            goginfo[k] = set_language(v)

    elif isinstance(goginfo, list):
        print("Fixing list info...")
        # Recurse into each list element
        goginfo = [set_language(x) for x in goginfo]

    elif isinstance(goginfo, str):
        print("Fixing str info...")
        # Apply regex replacement in strings
        goginfo = LOCALE_PATTERN.sub("-locale=us", goginfo)

    return goginfo

# Process a single installer (.exe)
def process_installer(installer):
    print(f"Extracting GOG game ID from {installer}...")
    try:
        result = subprocess.run(["innoextract", "--gog-game-id", str(installer)], capture_output=True, text=True)
        gog_game_id = next((line.split("ID is ")[-1] for line in result.stdout.splitlines() if "ID is " in line), None)
        if not gog_game_id:
            raise ValueError("No game ID found")
    except Exception as e:
        print(f"Error: Unable to extract GOG game ID: {e}")
        return
    
    # Fetch game metadata using the installer as the base game
    game_name, year = fetch_metadata(gog_game_id)
    game_name = game_name.title().replace("Ii","II").replace("IIi","III").replace("Iv","IV").replace("Vi","VI").replace("VIi","VII").replace("VIIi","VIII").replace("Ix","IX")
    if year == "0000":
        folder_name = f"{game_name} [GOG] (v) (W_P) (year)"
    else:
        folder_name = f"{game_name} [GOG] (v) (W_P) ({year})"
    folder_name = folder_name.replace(":", "")
    
    # Extract files to temp directory and archive them in destination
    temp_dir = Path(tempfile.mkdtemp(prefix="processing_", dir=TEMP_DIR))
    try:
        print(f"Extracting {installer}...")
        subprocess.run(["innoextract", "-gmsp", "-d", str(temp_dir), str(installer)], check=True)

        # Fixing language and locale if needed
        for goginfo in temp_dir.glob("goggame*.info"):
            if goginfo:
                print(f"Setting language in config file: {goginfo}")
                with open(goginfo, "r", encoding="utf-8") as f:
                    data = json.load(f)

                normalized = set_language(data)

                with open(goginfo, "w", encoding="utf-8") as f:
                    json.dump(normalized, f, indent=4, ensure_ascii=False)

        print(f"Creating rar archive in {DEST_DIR}...")
        rar_name = f"{folder_name}.rar"
        rar_file = DEST_DIR / rar_name
        game_files = temp_dir / "*"
        subprocess.run(["rar", "a", "-htb", "-rr", "-r", "-ep1", "-idcdn", str(rar_file), str(game_files)], check=True)
        print(f"Extraction, zipping, and cleanup completed successfully!")
        print(f"Archive: {DEST_DIR / rar_name}")
    except Exception as e:
        print(f"Error during extraction/archiving: {e}")
        return
    finally:
        print(f"Cleaning up {temp_dir}...")
        shutil.rmtree(temp_dir)
    
    processed_files.add(str(installer))
    save_processed_files(processed_files)

# Process all installers in a directory as one game (base game metadata is used)
def process_directory_game(game_dir):
    print(f"Processing game in directory: {game_dir}")
    base_installer = next(game_dir.glob("*.exe"), None)
    if not base_installer:
        print(f"No installer found in {game_dir}. Skipping.")
        return

    try:
        result = subprocess.run(["innoextract", "--gog-game-id", str(base_installer)], capture_output=True, text=True)
        gog_game_id = next((line.split("ID is ")[-1] for line in result.stdout.splitlines() if "ID is " in line), None)
        if not gog_game_id:
            raise ValueError("No game ID found")
    except Exception as e:
        print(f"Error: Unable to extract GOG game ID from {base_installer}: {e}")
        return

    # Fetch game metadata using the installer as the base game
    game_name, year = fetch_metadata(gog_game_id)
    game_name = game_name.title().replace("Ii","II").replace("IIi","III").replace("Iv","IV").replace("Vi","VI").replace("VIi","VII").replace("VIIi","VIII").replace("Ix","IX")
    if year == "0000":
        folder_name = f"{game_name} [GOG] (v) (W_P) (year)"
    else:
        folder_name = f"{game_name} [GOG] (v) (W_P) ({year})"
    folder_name = folder_name.replace(":", "")
    
    temp_dir = Path(tempfile.mkdtemp(prefix="processing_", dir=TEMP_DIR))
    try:
        for installer in game_dir.glob("*.exe"):
            if str(installer) in processed_files:
                continue
            print(f"Extracting {installer}...")
            subprocess.run(["innoextract", "-gmsp", "-d", str(temp_dir), str(installer)], check=True)

        # Fixing language and locale if needed
        for goginfo in temp_dir.glob("goggame*.info"):
            if goginfo:
                print(f"Setting language in config file: {goginfo}")
                with open(goginfo, "r", encoding="utf-8") as f:
                    data = json.load(f)

                normalized = set_language(data)

                with open(goginfo, "w", encoding="utf-8") as f:
                    json.dump(normalized, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error during extraction: {e}")
        shutil.rmtree(temp_dir)
        return

    try:
        if list(temp_dir.glob("*")):
            print(f"Creating rar archive in {DEST_DIR}...")
            rar_name = f"{folder_name}.rar"
            rar_file = DEST_DIR / rar_name
            game_files = temp_dir / "*"
            subprocess.run(["rar", "a", "-htb", "-rr", "-r", "-ep1", "-idcdn", str(rar_file), str(game_files)], check=True)
            print(f"Extraction, zipping, and cleanup completed successfully!")
            print(f"Archive: {DEST_DIR / rar_name}")
    finally:
        print(f"Cleaning up {temp_dir}...")
        shutil.rmtree(temp_dir)

    for installer in game_dir.glob("*.exe"):
        if str(installer) in processed_files:
            continue
        processed_files.add(str(installer))

    save_processed_files(processed_files)

# Process individual EXE files
if str(GOG_INPUT).lower().endswith(".exe"):
    if str(GOG_INPUT) not in processed_files:
        print(f"New installer detected: {GOG_INPUT}")
        process_installer(GOG_INPUT)
# Also check each subdirectory for EXE files
if GOG_INPUT.is_dir():
    exe_files_in_dir = list(GOG_INPUT.glob("*.exe"))
    if exe_files_in_dir:
        print(f"New installation folder detected: {GOG_INPUT}")
        process_directory_game(GOG_INPUT)
