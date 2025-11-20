"""
Daemon service for managing the file watcher in the background.
Provides commands to start, stop, status, and manage the watcher process.
"""

import os
import sys
import time
import json
import signal
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

# PID file location
PID_FILE = Path("watcher.pid")
STATUS_FILE = Path("watcher_status.json")


class WatcherDaemon:
    """
    Daemon manager for the file watcher service.
    Handles start, stop, status, and process management.
    """
    
    def __init__(self, watch_folder: str = "test_cases_output/reviewed"):
        """
        Initialize the daemon manager.
        
        Args:
            watch_folder: Folder to watch for Excel files
        """
        self.watch_folder = watch_folder
    
    def _read_pid(self) -> Optional[int]:
        """Read the PID from the PID file."""
        if not PID_FILE.exists():
            return None
        
        try:
            return int(PID_FILE.read_text().strip())
        except (ValueError, IOError):
            return None
    
    def _write_pid(self, pid: int):
        """Write the PID to the PID file."""
        PID_FILE.write_text(str(pid))
    
    def _remove_pid(self):
        """Remove the PID file."""
        if PID_FILE.exists():
            PID_FILE.unlink()
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running."""
        try:
            os.kill(pid, 0)  # Signal 0 just checks if process exists
            return True
        except (OSError, ProcessLookupError):
            return False
    
    def _update_status(self, status: str, message: str = ""):
        """Update the status file."""
        status_data = {
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "watch_folder": self.watch_folder,
            "pid": self._read_pid()
        }
        STATUS_FILE.write_text(json.dumps(status_data, indent=2))
    
    def _get_status(self) -> dict:
        """Get the current status."""
        if not STATUS_FILE.exists():
            return {
                "status": "unknown",
                "message": "No status file found",
                "running": False
            }
        
        try:
            status_data = json.loads(STATUS_FILE.read_text())
            pid = status_data.get("pid")
            
            if pid and self._is_process_running(pid):
                status_data["running"] = True
            else:
                status_data["running"] = False
                if status_data["status"] == "running":
                    status_data["status"] = "stopped"
                    status_data["message"] = "Process not found (may have crashed)"
            
            return status_data
        except (json.JSONDecodeError, IOError) as e:
            return {
                "status": "error",
                "message": f"Failed to read status: {e}",
                "running": False
            }
    
    def start(self) -> bool:
        """
        Start the file watcher service.
        
        Returns:
            True if started successfully, False otherwise
        """
        # Check if already running
        pid = self._read_pid()
        if pid and self._is_process_running(pid):
            print(f"File watcher is already running (PID: {pid})")
            return False
        
        # Clean up stale PID file
        if PID_FILE.exists():
            self._remove_pid()
        
        print("Starting file watcher service...")
        
        # Start the watcher process
        try:
            # Use current Python executable (works with virtual environments)
            python_exe = sys.executable
            
            # Create log file for background process
            log_file = Path("watcher.log")
            
            with open(log_file, "a") as log:
                process = subprocess.Popen(
                    [python_exe, "-m", "services.file_watcher", self.watch_folder],
                    stdout=log,
                    stderr=log,
                    start_new_session=True if sys.platform != "win32" else False,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
                )
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                pid = process.pid
                self._write_pid(pid)
                self._update_status("running", f"Started successfully on PID {pid}")
                print(f"File watcher started successfully (PID: {pid})")
                print(f"Watching folder: {self.watch_folder}")
                print(f"Log file: watcher.log")
                return True
            else:
                print("Failed to start file watcher (process exited immediately)")
                self._update_status("error", "Process exited immediately after start")
                return False
        
        except Exception as e:
            print(f"Error starting file watcher: {e}")
            self._update_status("error", str(e))
            return False
    
    def stop(self) -> bool:
        """
        Stop the file watcher service.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        pid = self._read_pid()
        
        if not pid:
            print("File watcher is not running (no PID file found)")
            return False
        
        if not self._is_process_running(pid):
            print("File watcher is not running (process not found)")
            self._remove_pid()
            self._update_status("stopped", "Process was not running")
            return False
        
        print(f"Stopping file watcher (PID: {pid})...")
        
        try:
            # Send SIGTERM to gracefully stop the process
            os.kill(pid, signal.SIGTERM)
            
            # Wait for process to stop (max 10 seconds)
            for _ in range(10):
                if not self._is_process_running(pid):
                    break
                time.sleep(1)
            
            # If still running, force kill
            if self._is_process_running(pid):
                print("Process did not stop gracefully, forcing...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(1)
            
            self._remove_pid()
            self._update_status("stopped", "Stopped by user")
            print("File watcher stopped successfully")
            return True
        
        except Exception as e:
            print(f"Error stopping file watcher: {e}")
            return False
    
    def restart(self) -> bool:
        """
        Restart the file watcher service.
        
        Returns:
            True if restarted successfully, False otherwise
        """
        print("Restarting file watcher...")
        self.stop()
        time.sleep(1)
        return self.start()
    
    def status(self):
        """Print the current status of the file watcher."""
        status = self._get_status()
        
        print("=" * 80)
        print("File Watcher Status")
        print("=" * 80)
        print(f"Status: {status['status']}")
        print(f"Running: {'Yes' if status.get('running') else 'No'}")
        if status.get('pid'):
            print(f"PID: {status['pid']}")
        if status.get('watch_folder'):
            print(f"Watch Folder: {status['watch_folder']}")
        if status.get('message'):
            print(f"Message: {status['message']}")
        if status.get('timestamp'):
            print(f"Last Updated: {status['timestamp']}")
        print("=" * 80)
    
    def logs(self, lines: int = 50):
        """
        Display the last N lines of the watcher log.
        
        Args:
            lines: Number of lines to display
        """
        log_file = Path("watcher.log")
        
        if not log_file.exists():
            print("No log file found")
            return
        
        print(f"Last {lines} lines of watcher.log:")
        print("=" * 80)
        
        try:
            with open(log_file, 'r') as f:
                log_lines = f.readlines()
                for line in log_lines[-lines:]:
                    print(line.rstrip())
        except Exception as e:
            print(f"Error reading log file: {e}")


def main():
    """Main entry point for the daemon CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Manage the TestRail file watcher daemon'
    )
    parser.add_argument(
        'command',
        choices=['start', 'stop', 'restart', 'status', 'logs'],
        help='Command to execute'
    )
    parser.add_argument(
        '--folder',
        default='test_cases_output/reviewed',
        help='Folder to watch (default: test_cases_output/reviewed)'
    )
    parser.add_argument(
        '--lines',
        type=int,
        default=50,
        help='Number of log lines to display (for logs command)'
    )
    
    args = parser.parse_args()
    
    daemon = WatcherDaemon(watch_folder=args.folder)
    
    if args.command == 'start':
        success = daemon.start()
        sys.exit(0 if success else 1)
    
    elif args.command == 'stop':
        success = daemon.stop()
        sys.exit(0 if success else 1)
    
    elif args.command == 'restart':
        success = daemon.restart()
        sys.exit(0 if success else 1)
    
    elif args.command == 'status':
        daemon.status()
        sys.exit(0)
    
    elif args.command == 'logs':
        daemon.logs(lines=args.lines)
        sys.exit(0)


if __name__ == '__main__':
    main()
