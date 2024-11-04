TubeArchivist Renamer
A script to rename .mp4 files based on YouTube video titles and organize them into channel-specific folders. This project is ideal for media libraries, allowing you to archive YouTube videos with descriptive titles and neatly sorted folders based on the originating YouTube channel.

    Features
    Fetches and uses YouTube video titles for renaming .mp4 files.
    Organizes videos into folders named after the YouTube channel.
    Customizable filename patterns (e.g., {title} - {channel_name}.mp4).
    Recursive scanning of directories.
    Optional integration with Plex to automatically update the media library.
    Configurable logging and scheduling options.
    Requirements
    Python 3.x
    Required Python libraries: requests, beautifulsoup4
    Install the necessary libraries using:

bash
    pip install requests beautifulsoup4

Configuration
The script uses a config.json file for setup, which includes directory paths, Plex settings, filename patterns, and other options. Here is an example configuration:

json

    {
    "plex_url": "http://localhost:32400",
    "plex_token": "YOUR_PLEX_TOKEN_HERE",
    "library_section_id": "1",
    "directory_paths": "/mnt/user/media/tubearchivist/",
    "scan_recursively": true,
    "title_length_limit": 50,
    "log_file_path": "/mnt/user/media/tubearchivist/renamed_files.log",
    "destination_folder": "",
    "wait_timer": 10,
    "schedule": "",
    "max_retries": 3,
    "retry_delay": 5,
    "filename_pattern": "{title} - {channel_name}.mp4",
    "max_log_entries": 1000,
    "metadata_log": "/mnt/user/media/tubearchivist/renamed_files.log"
    }

Configuration Options
    plex_url: Plex server URL (e.g., http://localhost:32400).
    plex_token: Plex API token for library refreshes.
    library_section_id: Plex library section ID to refresh.
    directory_paths: Comma-separated paths of directories with .mp4 files.
    scan_recursively: Set to true to scan subdirectories.
    title_length_limit: Maximum length of the video title used in filenames.
    log_file_path: Path to the log file for renaming actions.
    destination_folder: Directory for processed files. If empty, defaults to processed_files within the script’s directory.
    wait_timer: Time (in seconds) to wait between processing each file.
    schedule: Optional cron expression to run the script on a schedule.
    max_retries: Maximum retries for YouTube title fetch.
    retry_delay: Delay (in seconds) between retries.
    filename_pattern: Pattern for new file names. Supported placeholders:
    {title}: YouTube video title.
    {id}: Original filename (YouTube video ID).
    {date}: Current date.
    {original}: Original filename without extension.
    {channel_name}: Channel name of the video.
    max_log_entries: Limits the number of entries in the log.
    metadata_log: Path to a metadata log to track renamed files.

Usage
Command-Line Options
    -i or --interactive: Run in interactive mode, prompting before each rename.
    -d or --debug: Run in debug mode with verbose logging.
    -s or --setup: Set up the default config.json with recommended values.
    --dry-run: Simulate actions without making changes.
Running the Script
To execute the script, navigate to the script’s directory and run:

bash
    python3 youtube_title_renamer.py
To set up the configuration file if it doesn’t exist:

bash
    python3 youtube_title_renamer.py -s
Scheduling the Script
If you wish to schedule the script, specify a cron-formatted string in the schedule field in config.json. For example, to run every day at midnight:

json
    "schedule": "0 0 * * *"
Examples
Example Directory Structure
Assume the following structure in /mnt/user/media/tubearchivist/:

bash
    /mnt/user/media/tubearchivist/
    ├── UC6mIxFTvXkWQVEHPsEdflzQ/
    │   └── Axux_INFMZ4.mp4
    └── UC7I9mY0cU9kz7zAasXyxz0g/
        └── A6g7hD5s.mp4

When the script processes this structure, it will:

Retrieve the channel name for each folder (e.g., "GreatScott" for UC6mIxFTvXkWQVEHPsEdflzQ).
Create a folder for each channel in destination_folder.
Rename and copy each .mp4 file based on the specified filename_pattern.
Example Output
With filename_pattern set to {title} - {channel_name}.mp4, the output in the destination folder may look like this:

bash
    /processed_files/
    ├── GreatScott/
    │   └── July 26, 2023, House UAP Hearing - GreatScott.mp4
    └── AnotherChannel/
        └── VideoTitle - AnotherChannel.mp4
Logging
The script logs all operations to log_file_path specified in config.json. Logs include the original and renamed filenames, processing times, and error messages if any issues arise.

Troubleshooting
Config File Not Found: Ensure config.json is in the same directory as the script.
YouTube Title Fetch Fails: Check network connectivity or YouTube API status.
Plex Refresh Fails: Verify plex_url and plex_token are correctly set.
For additional debug information, use the -d flag to see detailed logging output.

License
This project is licensed under the MIT License.

This README should cover the core aspects of the project, setup instructions, and usage examples. Let me know if there are any specific details you would like to expand or clarify!