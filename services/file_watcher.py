"""
File Watcher Service for TestRail Sync
Monitors the reviewed/ folder for new Excel files and automatically triggers sync.
"""

import os
import time
import logging
import shutil
from pathlib import Path
from typing import Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent

from services.sync_service import TestRailSyncService
from integrations.testrail_config import TestRailConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExcelFileHandler(FileSystemEventHandler):
    """
    Handles file system events for Excel files in the reviewed folder.
    Triggers sync when new Excel files are detected.
    """
    
    def __init__(
        self,
        sync_service: TestRailSyncService,
        processed_folder: Path,
        errors_folder: Path,
        on_sync_complete: Optional[Callable] = None
    ):
        """
        Initialize the file handler.
        
        Args:
            sync_service: TestRailSyncService instance for syncing
            processed_folder: Folder to move successfully processed files
            errors_folder: Folder to move files that failed to sync
            on_sync_complete: Optional callback after sync completes
        """
        self.sync_service = sync_service
        self.processed_folder = processed_folder
        self.errors_folder = errors_folder
        self.on_sync_complete = on_sync_complete
        self.processing_files = set()  # Track files currently being processed
        
        # Ensure output folders exist
        self.processed_folder.mkdir(parents=True, exist_ok=True)
        self.errors_folder.mkdir(parents=True, exist_ok=True)
    
    def _is_excel_file(self, file_path: str) -> bool:
        """Check if file is an Excel file and not a temp file."""
        path = Path(file_path)
        return (
            path.suffix.lower() == '.xlsx' and
            not path.name.startswith('~$') and
            not path.name.startswith('.')
        )
    
    def _wait_for_file_ready(self, file_path: Path, timeout: int = 30) -> bool:
        """
        Wait for file to be completely written and ready for processing.
        
        Args:
            file_path: Path to the file
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if file is ready, False if timeout
        """
        start_time = time.time()
        last_size = -1
        
        while time.time() - start_time < timeout:
            try:
                current_size = file_path.stat().st_size
                if current_size == last_size and current_size > 0:
                    # Size hasn't changed, file is ready
                    time.sleep(0.5)  # Extra buffer
                    return True
                last_size = current_size
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Error checking file size: {e}")
                time.sleep(1)
        
        return False
    
    def _process_file(self, file_path: str):
        """
        Process an Excel file by syncing it to TestRail.
        
        Args:
            file_path: Path to the Excel file to process
        """
        path = Path(file_path)
        
        # Skip if already processing
        if str(path) in self.processing_files:
            logger.debug(f"File already being processed: {path.name}")
            return
        
        # Skip if not Excel
        if not self._is_excel_file(file_path):
            logger.debug(f"Skipping non-Excel file: {path.name}")
            return
        
        try:
            self.processing_files.add(str(path))
            logger.info(f"Detected new file: {path.name}")
            
            # Wait for file to be fully written
            if not self._wait_for_file_ready(path):
                logger.warning(f"Timeout waiting for file to be ready: {path.name}")
                return
            
            # Sync the file
            logger.info(f"Starting sync for: {path.name}")
            result = self.sync_service.sync_file(str(path))
            
            if result['status'] == 'success':
                # Move to processed folder
                destination = self.processed_folder / path.name
                logger.info(f"Sync successful! Moving to processed: {path.name}")
                logger.info(f"  Created: {result['created']}, Errors: {result['errors']}")
                
                # Retry moving file with exponential backoff (Windows file locking workaround)
                max_attempts = 10
                moved = False
                for attempt in range(max_attempts):
                    try:
                        # Check if source file still exists
                        if not path.exists():
                            logger.warning(f"Source file already moved or deleted: {path.name}")
                            moved = True
                            break
                        
                        # Attempt to move the file
                        shutil.move(str(path), str(destination))
                        logger.info(f"Successfully moved file to processed folder")
                        moved = True
                        break
                    except PermissionError as e:
                        wait_time = min(2 ** attempt, 10)  # Exponential backoff, max 10 seconds
                        if attempt < max_attempts - 1:
                            logger.warning(f"File locked, retrying in {wait_time}s... (attempt {attempt+1}/{max_attempts})")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"Failed to move file after {max_attempts} attempts: {e}")
                            logger.error(f"File remains in reviewed folder: {path}")
                            # Don't raise - file was successfully synced, just couldn't be moved
                
                if moved and self.on_sync_complete:
                    self.on_sync_complete(str(destination), result)
            else:
                # Move to errors folder
                destination = self.errors_folder / path.name
                logger.error(f"Sync failed! Moving to errors: {path.name}")
                logger.error(f"  Error: {result.get('error', 'Unknown error')}")
                
                # Retry moving file with exponential backoff (Windows file locking workaround)
                max_attempts = 10
                moved = False
                for attempt in range(max_attempts):
                    try:
                        # Check if source file still exists
                        if not path.exists():
                            logger.warning(f"Source file already moved or deleted: {path.name}")
                            moved = True
                            break
                        
                        # Attempt to move the file
                        shutil.move(str(path), str(destination))
                        logger.info(f"Successfully moved file to errors folder")
                        moved = True
                        break
                    except PermissionError as e:
                        wait_time = min(2 ** attempt, 10)  # Exponential backoff, max 10 seconds
                        if attempt < max_attempts - 1:
                            logger.warning(f"File locked, retrying in {wait_time}s... (attempt {attempt+1}/{max_attempts})")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"Failed to move file after {max_attempts} attempts: {e}")
                            logger.error(f"File remains in reviewed folder: {path}")
                            # Don't raise - just log the error
                
                if moved and self.on_sync_complete:
                    self.on_sync_complete(str(destination), result)
        
        except Exception as e:
            logger.error(f"Error processing file {path.name}: {e}", exc_info=True)
            
            # Try to move to errors folder with retry logic
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    if not path.exists():
                        logger.warning(f"Source file already moved or deleted: {path.name}")
                        break
                    
                    destination = self.errors_folder / path.name
                    shutil.move(str(path), str(destination))
                    logger.info(f"Moved failed file to errors: {path.name}")
                    break
                except PermissionError as move_error:
                    wait_time = min(2 ** attempt, 5)
                    if attempt < max_attempts - 1:
                        logger.warning(f"Cannot move file, retrying in {wait_time}s... (attempt {attempt+1}/{max_attempts})")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Failed to move file to errors after {max_attempts} attempts: {move_error}")
                        logger.error(f"File remains in reviewed folder: {path}")
                except Exception as move_error:
                    logger.error(f"Failed to move file to errors: {move_error}")
                    break
        
        finally:
            self.processing_files.discard(str(path))
    
    def on_created(self, event: FileCreatedEvent):
        """Handle file creation events."""
        if not event.is_directory:
            self._process_file(event.src_path)
    
    def on_moved(self, event: FileMovedEvent):
        """Handle file move events (e.g., drag-and-drop into folder)."""
        if not event.is_directory:
            self._process_file(event.dest_path)


class FileWatcherService:
    """
    Service to watch a folder for new Excel files and automatically sync them.
    """
    
    def __init__(
        self,
        watch_folder: str,
        config: Optional[TestRailConfig] = None,
        on_sync_complete: Optional[Callable] = None
    ):
        """
        Initialize the file watcher service.
        
        Args:
            watch_folder: Path to folder to watch for new Excel files
            config: TestRail configuration (loads from env if not provided)
            on_sync_complete: Optional callback when sync completes
        """
        self.watch_folder = Path(watch_folder)
        self.config = config or TestRailConfig()
        self.sync_service = TestRailSyncService(self.config)
        self.on_sync_complete = on_sync_complete
        
        # Create folder structure
        self.watch_folder.mkdir(parents=True, exist_ok=True)
        self.processed_folder = self.watch_folder.parent / "processed"
        self.errors_folder = self.watch_folder.parent / "errors"
        
        # Setup file handler and observer
        self.event_handler = ExcelFileHandler(
            sync_service=self.sync_service,
            processed_folder=self.processed_folder,
            errors_folder=self.errors_folder,
            on_sync_complete=on_sync_complete
        )
        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            str(self.watch_folder),
            recursive=False
        )
        
        logger.info(f"File watcher initialized")
        logger.info(f"  Watching: {self.watch_folder}")
        logger.info(f"  Processed: {self.processed_folder}")
        logger.info(f"  Errors: {self.errors_folder}")
    
    def process_existing_files(self):
        """Process any Excel files that already exist in the watched folder."""
        logger.info("Checking for existing Excel files...")
        excel_files = list(self.watch_folder.glob("*.xlsx")) + list(self.watch_folder.glob("*.xls"))
        
        if excel_files:
            logger.info(f"Found {len(excel_files)} existing Excel file(s) to process")
            for excel_file in excel_files:
                logger.info(f"Processing existing file: {excel_file.name}")
                self.event_handler._process_file(str(excel_file))
        else:
            logger.info("No existing Excel files found")
    
    def start(self):
        """Start watching the folder."""
        logger.info("Starting file watcher...")
        
        # Process any existing files first
        self.process_existing_files()
        
        # Start watching for new files
        self.observer.start()
        logger.info("File watcher started. Monitoring for new Excel files...")
    
    def stop(self):
        """Stop watching the folder."""
        logger.info("Stopping file watcher...")
        self.observer.stop()
        self.observer.join()
        logger.info("File watcher stopped.")
    
    def run(self):
        """
        Run the file watcher in blocking mode with polling fallback.
        This will keep the process running until interrupted.
        
        Note: Polling is used as a fallback because Docker bind mounts on Windows
        don't properly propagate file system events to Linux containers.
        """
        self.start()
        poll_interval = 30  # Check every 30 seconds for new files
        last_poll = time.time()
        
        try:
            while True:
                time.sleep(1)
                
                # Periodic polling as fallback for Docker on Windows
                if time.time() - last_poll >= poll_interval:
                    logger.debug("Polling for new files (Docker Windows fallback)...")
                    self.process_existing_files()
                    last_poll = time.time()
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal...")
            self.stop()


def main():
    """Main entry point for running the file watcher as a standalone service."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Watch folder for Excel files and sync to TestRail'
    )
    parser.add_argument(
        'watch_folder',
        nargs='?',
        default='test_cases_output/reviewed',
        help='Folder to watch for Excel files (default: test_cases_output/reviewed)'
    )
    args = parser.parse_args()
    
    # Create and run watcher
    watcher = FileWatcherService(watch_folder=args.watch_folder)
    
    print("=" * 80)
    print("TestRail File Watcher Service")
    print("=" * 80)
    print(f"Watching folder: {watcher.watch_folder}")
    print(f"Processed files will be moved to: {watcher.processed_folder}")
    print(f"Failed files will be moved to: {watcher.errors_folder}")
    print("=" * 80)
    print("Press Ctrl+C to stop the service")
    print("=" * 80)
    print()
    
    watcher.run()


if __name__ == '__main__':
    main()
