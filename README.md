GOGtoGV

This script automates the process of extracting, processing, and archiving GOG game installers. It watches a specified directory for new .exe files, processes the installers by extracting metadata from the GOG API, creates a zip archive, and moves the processed files to designated folders.
Features

Automatic Folder Watching: Watches a specified directory for new .exe files.
- GOG Game Metadata: Extracts game metadata using the GOG API, including the game title and release year.
- Innoextract Support: Uses innoextract to extract .exe files related to GOG game installers.
- Zip Archive Creation: Archives the extracted files into a zip file for easy storage or distribution.
- File Organization: Organizes the processed files in a structured folder format with metadata.
- Persistence: Keeps track of processed files in a processed_files.json file to avoid reprocessing the same files.

Prerequisites

- Python 3.x
- innoextract (Windows users will need innoextract.exe)
- A valid config.ini configuration file.


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

The script will continuously watch the watch_dir for new .exe files. When a new installer is detected, it will:

Extract game metadata.
Create a zip archive of the extracted files.
Organize and move the files to the processed_dir
