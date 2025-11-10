#!/usr/bin/env python3
"""CLI tool for manual sync operations."""

import argparse
import json
import sys
from data_pipeline.sync_api import sync_api


def main():
    parser = argparse.ArgumentParser(description="QA Agent Vector Store Sync Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Rebuild vector store")
    sync_parser.add_argument(
        "--directories", 
        nargs="+", 
        help="Directories to process (default: from config)"
    )
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check vector store status")
    
    args = parser.parse_args()
    
    if args.command == "sync":
        print("Starting vector store sync...")
        result = sync_api.sync(args.directories)
        print(json.dumps(result, indent=2))
        if result["status"] == "error":
            sys.exit(1)
    
    elif args.command == "status":
        result = sync_api.status()
        print(json.dumps(result, indent=2))
        if result["status"] == "error":
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()