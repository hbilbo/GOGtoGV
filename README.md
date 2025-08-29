GOGtoGV

This script automates the process of extracting, processing, and archiving GOG game installers. When run it checks a specified directory for new .exe files, processes the installers by extracting metadata from the GOG API, creates a rar archive, and moves the processed files to designated folders.
Features

- GOG Game Metadata: Extracts game metadata using the GOG API, including the game title and release year.
- Innoextract Support: Uses innoextract to extract .exe files related to GOG game installers.
- Rar Archive Creation: Archives the extracted files into a rar file with recovery record for easy storage or distribution.
- File Organization: Organizes the processed files in a structured folder format with metadata.
- Persistence: Keeps track of processed files in a processed_files.json file to avoid reprocessing the same files.

Prerequisites

- Python 3.x
- innoextract installed on the system and in PATH
- rar installed on the system and in PATH
- A valid config.ini configuration file.

*Note: Docker is not currently supported for this repo*

Usage

Configuration File:
    The script uses a config.ini file to define directory paths for watching, processing, and archiving files.

Example config.ini:

    [folders]
    watch_dir = /path/to/watched/dir
    dest_dir = /path/to/destination/dir
    processed_dir = processed

Run the script:

python main.py

The script will check the watch_dir for new .exe files. When a new installer is detected, it will:

Extract game metadata.
Create a rar archive of the extracted files.
Organize and move the files to the processed_dir
