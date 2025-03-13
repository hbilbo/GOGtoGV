import os
import sys
import shutil
import subprocess
import requests
import json
import tempfile
import time
from pathlib import Path
import zipfile
import configparser

# Load configuration from ini file
config = configparser.ConfigParser()
config.read('config.ini')

# Get folder paths from config or use default
WATCH_DIR = Path(config.get('folders', 'watch_dir', fallback="/WATCHED"))
DEST_DIR = Path(config.get('folders', 'dest_dir', fallback="/DEST"))
PROCESSED_JSON = WATCH_DIR / "processed_files.json"
PROCESSED_DIR = Path(config.get('folders', 'processed_dir', fallback="processed"))

# Ensure necessary directories exist
DEST_DIR.mkdir(parents=True, exist_ok=True)
(WATCH_DIR / PROCESSED_DIR).mkdir(parents=True, exist_ok=True)

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

    game_title = data.get("title", "Unknown Game")
    release_date = data.get("release_date", "0000")

    if release_date:
        year = release_date.split("-")[0]  # Extract year
    else:
        year = "0000"  # Default if release_date is None

    return game_title, year

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
    
    # Fetch game metadata
    game_name, year = fetch_metadata(gog_game_id)
    
    # Create folder name and exclude year if it's '0000'
    if year == "0000":
        folder_name = f"{game_name} (W_P)"
    else:
        folder_name = f"{game_name} (W_P) ({year})"
    
    folder_name = folder_name.replace(":", "")  # Remove dashes from folder name
    
    # Create a subfolder inside processed folder named after the game
    game_folder = WATCH_DIR / PROCESSED_DIR / folder_name
    game_folder.mkdir(parents=True, exist_ok=True)

    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        print(f"Extracting {installer}...")
        subprocess.run(["innoextract", "--gog", "--exclude-temp", "--output-dir", str(temp_dir), str(installer)], check=True)
        
        print(f"Creating zip archive in {DEST_DIR}...")
        zip_name = f"{folder_name}.zip"
        with zipfile.ZipFile(DEST_DIR / zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = Path(root) / file
                    zipf.write(file_path, file_path.relative_to(temp_dir))
        
        print(f"Extraction, zipping, and cleanup completed successfully!")
        print(f"Archive: {DEST_DIR / zip_name}")
    finally:
        print(f"Cleaning up {temp_dir}...")
        shutil.rmtree(temp_dir)
    
    # Move processed installer and bin files to the game folder inside processed
    processed_path = game_folder / installer.name
    installer.rename(processed_path)
    print(f"Moved {installer} to {processed_path}.")
    
    # Move .bin files
    for bin_file in WATCH_DIR.glob(installer.stem + "-*.bin"):
        bin_file.rename(game_folder / bin_file.name)
        print(f"Moved {bin_file} to {game_folder / bin_file.name}.")
    
    # Add to processed files list and save
    processed_files.add(str(installer))
    save_processed_files(processed_files)

# Watch the folder for new EXE files
def watch_folder():
    print(f"Watching {WATCH_DIR} for new EXE files...")
    
    while True:
        for exe_file in WATCH_DIR.glob("*.exe"):
            if str(exe_file) not in processed_files:
                print(f"New installer detected: {exe_file}")
                process_installer(exe_file)
        time.sleep(5)

if __name__ == "__main__":
    watch_folder()
