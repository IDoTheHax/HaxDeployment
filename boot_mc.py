import os
import subprocess
import time
from datetime import datetime, timedelta

# Configuration Parameters
BACKUP_INTERVAL_HOURS = 12  # Interval between backups in hours
PURGE_INTERVAL_HOURS = 24  # Interval between crash log purges in hours
SERVER_MEMORY_MIN = "1G"  # Minimum memory allocation for the server
SERVER_MEMORY_MAX = "7G"  # Maximum memory allocation for the server
SERVER_JAR_PATH = os.path.expanduser("~/solar-smp/server.jar")
SERVER_SCREEN_NAME = "solar"
BACKUP_BASE_DIR = os.path.expanduser("~/")
SERVER_DIR = os.path.expanduser("~/solar-smp/")
BACKUP_DIR_PREFIX = "autobackup-"

def start_server():
    """Starts the Minecraft server in a detached screen session."""
    print("[Server] Starting Minecraft server...")
    subprocess.run([
        "screen", "-dmS", SERVER_SCREEN_NAME,
        "java", f"-Xms{SERVER_MEMORY_MIN}", f"-Xmx{SERVER_MEMORY_MAX}",
        "-jar", SERVER_JAR_PATH
    ])

def perform_autobackup():
    """Performs a backup of the Minecraft server data."""
    print("[Auto Backup] Initiating backup...")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_folder = os.path.join(BACKUP_BASE_DIR, f"{BACKUP_DIR_PREFIX}{timestamp}")
    os.makedirs(backup_folder, exist_ok=True)
    
    # List of files/folders to backup
    items_to_backup = [
        os.path.join(SERVER_DIR, "solar3"),
        os.path.join(SERVER_DIR, "banned-ips.json"),
        os.path.join(SERVER_DIR, "banned-players.json"),
        os.path.join(SERVER_DIR, "config"),
    ]
    for item in items_to_backup:
        if os.path.exists(item):
            if os.path.isdir(item):
                subprocess.run(["cp", "-r", item, backup_folder])
            else:
                subprocess.run(["cp", item, backup_folder])
    
    print("[Auto Backup] Backup completed successfully.")

def purge_crash_logs():
    """Deletes crash logs from the crash-reports directory."""
    crash_reports_dir = os.path.join(SERVER_DIR, "crash-reports")
    print("[Server] Purging crash logs...")
    if os.path.exists(crash_reports_dir):
        for file in os.listdir(crash_reports_dir):
            file_path = os.path.join(crash_reports_dir, file)
            os.remove(file_path)
    print("[Server] Purged crash logs successfully.")

def check_recent_backup():
    """Checks if a backup was done in the last specified interval."""
    cutoff_time = datetime.now() - timedelta(hours=BACKUP_INTERVAL_HOURS)
    for dir_name in os.listdir(BACKUP_BASE_DIR):
        if dir_name.startswith(BACKUP_DIR_PREFIX):
            timestamp_str = dir_name.replace(BACKUP_DIR_PREFIX, "")
            try:
                backup_time = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
                if backup_time >= cutoff_time:
                    print(f"[Auto Backup] Recent backup found: {dir_name}")
                    return True
            except ValueError:
                continue
    print("[Auto Backup] No recent backup found.")
    return False

def is_server_running():
    """Checks if the server is running."""
    result = subprocess.run(["screen", "-list"], capture_output=True, text=True)
    return SERVER_SCREEN_NAME in result.stdout

def main():
    """Main function to monitor and manage the Minecraft server."""
    last_backup_time = time.time()
    last_purge_time = time.time()

    while True:
        current_time = time.time()

        # Perform backup if necessary
        if current_time - last_backup_time >= BACKUP_INTERVAL_HOURS * 3600:
            if not check_recent_backup():
                perform_autobackup()
                last_backup_time = current_time
            else:
                print("[Auto Backup] Skipping backup as one was recently completed.")

        # Purge crash logs if necessary
        if current_time - last_purge_time >= PURGE_INTERVAL_HOURS * 3600:
            purge_crash_logs()
            last_purge_time = current_time

        # Restart server if not running
        if not is_server_running():
            print("[Server] Server not running. Restarting...")
            start_server()

        # Sleep before checking again
        time.sleep(10)

if __name__ == "__main__":
    main()
