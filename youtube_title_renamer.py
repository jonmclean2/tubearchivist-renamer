#!/usr/bin/env python3

import os
import json
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import logging
from datetime import datetime
import argparse
import subprocess
import re

# CONFIGURATION GUIDE:
# - plex_url: URL of your Plex server (e.g., "http://localhost:32400").
# - plex_token: Your Plex API token for authentication.
# - library_section_id: The ID of the Plex library section to scan.
# - directory_paths: Comma-separated paths of directories to scan for .mp4 files.
# - scan_recursively: Set to true to enable recursive scanning of subdirectories; set to false to scan only top-level directories.
# - title_length_limit: Limit on the number of characters for the video title when renaming files (recommended: 50).
# - log_file_path: Path to the log file where rename actions will be recorded.
# - wait_timer: Time in seconds to wait between processing each video (recommended: 10).
# - schedule: Optional cron-formatted string for automatic scheduling.
# - max_retries: Maximum number of attempts to retry fetching the YouTube title (recommended: 3).
# - retry_delay: Delay in seconds between retry attempts (recommended: 5).
# - filename_pattern: Pattern for renaming files. Supported placeholders: {title}, {video_id}, {date}.
# - max_log_entries: Number of log entries to retain in the log file.

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Rename .mp4 files with YouTube video titles.")
parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
parser.add_argument("-d", "--debug", action="store_true", help="Run in debug mode with verbose output")
parser.add_argument("-s", "--setup", action="store_true", help="Set up config.json with default values and ensure required libraries")
parser.add_argument("--dry-run", action="store_true", help="Simulate actions without making changes")
args = parser.parse_args()
interactive_mode = args.interactive
debug_mode = args.debug
setup_mode = args.setup
dry_run = args.dry_run

# Determine script directory and config path
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")

# Load configuration from config.json
try:
    with open(config_path) as f:
        config = json.load(f)
    print("Configuration loaded successfully:", config)  # Debug statement
except FileNotFoundError:
    print("Error: config.json file not found.")
    exit(1)
except json.JSONDecodeError:
    print("Error: config.json file is not properly formatted.")
    exit(1)

# Default configuration values
default_config = {
    "plex_url": "http://localhost:32400",
    "plex_token": "YOUR_PLEX_TOKEN_HERE",
    "library_section_id": "1",
    "directory_paths": "/mnt/user/media/tubearchivist/",
    "scan_recursively": True,
    "title_length_limit": 50,
    "log_file_path": "/mnt/user/media/tubearchivist/renamed_files.log",
    "wait_timer": 10,
    "schedule": "",
    "max_retries": 3,
    "retry_delay": 5,
    "filename_pattern": "{title}.mp4",
    "max_log_entries": 1000,
    "metadata_log": "/mnt/user/media/tubearchivist/renamed_files.log"
}

def create_default_config():
    """Create config.json with default values and ensure required libraries are installed."""
    if os.path.exists(config_path):
        overwrite = input("config.json already exists. Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Setup canceled. Using existing config.json.")
            return
    
    with open(config_path, "w") as f:
        json.dump(default_config, f, indent=4)
    print("config.json created with default values.")
    
    # Ensure required libraries are installed
    ensure_libraries_installed()
    
    # Set up cron job if a schedule is provided
    if default_config["schedule"]:
        schedule_cron_job()

def ensure_libraries_installed():
    """Ensure required libraries are installed."""
    try:
        import requests
        import bs4
    except ImportError:
        print("Installing required libraries...")
        subprocess.run(["pip", "install", "requests", "beautifulsoup4"], check=True)

def schedule_cron_job():
    """Add a cron job based on the schedule in config.json."""
    schedule = config.get("schedule", "").strip()
    
    if schedule:
        cron_command = f"{schedule} python3 {Path(__file__).resolve()}"
        existing_crontab = subprocess.run("crontab -l", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if cron_command in existing_crontab.stdout:
            overwrite = input("A cron job for this script already exists. Overwrite? (y/n): ").strip().lower()
            if overwrite != 'y':
                print("Skipping cron setup.")
                return
        
        # Add or overwrite the cron job
        cron_job = f'(crontab -l | grep -v "{cron_command}"; echo "{cron_command}") | crontab -'
        subprocess.run(cron_job, shell=True, check=True)
        print(f"Cron job set up with schedule: {schedule}")

def fetch_youtube_title(video_id, max_retries, retry_delay):
    """Fetch the title of a YouTube video using its video ID with retry mechanism."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    for attempt in range(max_retries):
        if debug_mode:
            print(f"[DEBUG] Fetching URL: {url}, Attempt: {attempt + 1}")
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.text.replace(" - YouTube", "").strip()
                if debug_mode:
                    print(f"[DEBUG] Extracted title: {title}")
                return title
        time.sleep(retry_delay)
    logging.warning(f"Failed to fetch title for video ID {video_id} after {max_retries} attempts")
    return None

def sanitize_filename(filename):
    """Remove invalid characters from a filename."""
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    if not sanitized.strip():
        sanitized = "unnamed_file"
    return sanitized

def is_already_renamed(video_id):
    """Check if the video ID is already logged in renamed_files.log."""
    metadata_log_path = Path(config.get("metadata_log", "/tmp/renamed_files.log"))
    if not metadata_log_path.exists():
        return False
    with open(metadata_log_path, "r") as f:
        return any(video_id in line for line in f)

def log_renamed_file(video_id, new_name):
    """Log the renamed file in the metadata log to avoid reprocessing."""
    metadata_log_path = Path(config.get("metadata_log", "/tmp/renamed_files.log"))
    with open(metadata_log_path, "a") as f:
        f.write(f"{video_id},{new_name}\n")

def trim_title(title):
    """Trim the title to the specified length and ensure it ends on a word boundary."""
    title_length_limit = config.get("title_length_limit", 50)
    if len(title) <= title_length_limit:
        return title
    trimmed = title[:title_length_limit].rsplit(' ', 1)[0]
    if debug_mode:
        print(f"[DEBUG] Trimmed title: {trimmed}")
    return trimmed

def apply_filename_pattern(pattern, title, video_id):
    """Apply the filename pattern from config.json."""
    date_str = datetime.now().strftime("%Y%m%d")
    sanitized_title = sanitize_filename(title)
    return pattern.format(title=sanitized_title, video_id=video_id, date=date_str)

def rotate_log_file():
    """Keep only the last N entries in the log file."""
    log_file_path = config.get("log_file_path", "/tmp/logfile.log")
    max_log_entries = config.get("max_log_entries", 1000)
    
    with open(log_file_path, "r+") as log_file:
        lines = log_file.readlines()
        if len(lines) > max_log_entries:
            log_file.seek(0)
            log_file.writelines(lines[-max_log_entries:])
            log_file.truncate()

def rename_file(file_path, new_name):
    """Rename the file with a unique name to avoid conflicts."""
    if dry_run:
        print(f"[DRY RUN] Would rename '{file_path}' to '{new_name}'")
        return
    
    directory = file_path.parent
    new_file_path = directory / new_name
    counter = 1
    while new_file_path.exists():
        new_file_path = directory / f"{new_name}_{counter}.mp4"
        counter += 1
    os.rename(file_path, new_file_path)
    logging.info(f"Renamed '{file_path}' to '{new_file_path}'")
    if debug_mode:
        print(f"[DEBUG] Renamed '{file_path}' to '{new_file_path}'")

# Function to trigger a Plex library scan
def trigger_plex_scan():
    """Trigger a scan on the specified Plex library section."""
    plex_url = config.get("plex_url", "http://localhost:32400")
    plex_token = config.get("plex_token", "")
    library_section_id = config.get("library_section_id", "")
    
    if not plex_token or not library_section_id:
        print("Plex token or library section ID missing in config.json. Skipping Plex scan.")
        return

    headers = {
        "X-Plex-Token": plex_token
    }
    scan_url = f"{plex_url.rstrip('/')}/library/sections/{library_section_id}/refresh"
    
    try:
        response = requests.get(scan_url, headers=headers)
        if response.status_code == 200:
            print("Triggered Plex library scan successfully.")
            logging.info("Triggered Plex library scan successfully.")
        else:
            print(f"Failed to trigger Plex scan. Status code: {response.status_code}")
            logging.error(f"Failed to trigger Plex scan. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error triggering Plex scan: {e}")
        logging.error(f"Error triggering Plex scan: {e}")

def process_directory(path):
    """Process .mp4 files in a directory according to the configuration."""
    scan_recursively = config.get("scan_recursively", True)
    filename_pattern = config.get("filename_pattern", "{title}.mp4")
    wait_timer = config.get("wait_timer", 10)
    max_retries = config.get("max_retries", 3)
    retry_delay = config.get("retry_delay", 5)

    for root, _, files in os.walk(path) if scan_recursively else [(path, [], os.listdir(path))]:
        for file in files:
            if file.endswith(".mp4"):
                file_path = Path(root) / file
                video_id = file_path.stem
                print(f"\nProcessing video ID: {video_id}")

                # Check if the file has already been renamed
                if is_already_renamed(video_id):
                    print(f"[INFO] Skipping '{file}' (already renamed).")
                    continue

                # Fetch and trim the title
                title = fetch_youtube_title(video_id, max_retries, retry_delay)
                if title:
                    trimmed_title = trim_title(title)
                    new_name = apply_filename_pattern(filename_pattern, trimmed_title, video_id)

                    if interactive_mode:
                        # Confirm each rename in interactive mode
                        confirm = input(f"Rename '{file}' to '{new_name}'? (y/n): ").strip().lower()
                        if confirm != 'y':
                            print("Skipping file.")
                            continue

                    rename_file(file_path, new_name)
                    print(f"Renamed '{file}' to '{new_name}'")
                    log_renamed_file(video_id, new_name)
                    rotate_log_file()
                    time.sleep(wait_timer)

    # Trigger Plex scan after processing all files in the directory
    trigger_plex_scan()

# Run setup if -s flag is provided
if setup_mode:
    create_default_config()
    exit(0)

# Load settings from config.json
directory_paths = config.get("directory_paths", "").split(",")
log_file_path = config.get("log_file_path", "/mnt/user/media/tubearchivist/renamed_files.log")

# Set up logging with debug level based on the mode
log_level = logging.DEBUG if debug_mode else logging.INFO
logging.basicConfig(filename=log_file_path, level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting YouTube title renaming process")

# Process each specified directory
for directory in directory_paths:
    path = Path(directory.strip())
    if path.is_dir():
        print(f"\nScanning directory: {path}")
        process_directory(path)
    else:
        logging.warning(f"Directory '{path}' does not exist. Skipping.")
        if debug_mode:
            print(f"[DEBUG] Directory '{path}' does not exist. Skipping.")

logging.info("YouTube title renaming process completed")
print("YouTube title renaming process completed")
