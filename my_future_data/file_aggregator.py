#!/usr/bin/env python3
"""
File aggregator script to organize files based on their prefixes.

This script moves files from for_struct/ directory to:
- data/struct/ if filename starts with structured_text_
- data/raw/ if filename starts with transcription_
"""

import shutil
from pathlib import Path


def get_files_by_prefix(directory: Path) -> dict[str, list[Path]]:
    """
    Get files from directory categorized by their prefixes.

    Args:
        directory: Directory path to scan

    Returns:
        Dictionary mapping prefixes to lists of Path objects
    """
    result: dict[str, list[Path]] = {
        "structured_text_": [],
        "transcription_": [],
    }

    try:
        for file_path in directory.iterdir():
            if file_path.is_file():
                if file_path.name.startswith("structured_text_"):
                    result["structured_text_"].append(file_path)
                elif file_path.name.startswith("transcription_"):
                    result["transcription_"].append(file_path)
    except FileNotFoundError:
        print(f"Error: Directory '{directory}' not found.")

    return result


def ensure_directories_exist(directories: list[Path]) -> None:
    """
    Ensure that all specified directories exist, creating them if necessary.

    Args:
        directories: List of directory paths to check/create
    """
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def move_files(files_by_prefix: dict[str, list[Path]], source_dir: Path) -> tuple[int, int]:
    """
    Move files to their target directories based on prefix.

    Args:
        files_by_prefix: Dictionary mapping prefixes to lists of Path objects
        source_dir: Source directory containing the files

    Returns:
        Tuple containing count of successful and failed moves
    """
    target_dirs = {
        "structured_text_": Path("data/struct"),
        "transcription_": Path("data/raw"),
    }

    ensure_directories_exist(list(target_dirs.values()))

    success_count = 0
    error_count = 0

    for prefix, files in files_by_prefix.items():
        target_dir = target_dirs.get(prefix)
        if not target_dir:
            continue

        for file_path in files:
            target_path = target_dir / file_path.name

            try:
                # Check if target file already exists
                if target_path.exists():
                    print(f"Warning: File already exists at {target_path}, skipping...")
                    error_count += 1
                    continue

                # Move file instead of copying
                shutil.move(str(file_path), str(target_path))
                print(f"Moved: {file_path.name} -> {target_dir}")
                success_count += 1
            except Exception as e:
                print(f"Error moving {file_path.name}: {str(e)}")
                error_count += 1

    return success_count, error_count


def main() -> None:
    """Main function to aggregate files."""
    source_dir = Path("for_struct")

    print(f"Scanning directory: {source_dir}")
    files_by_prefix = get_files_by_prefix(source_dir)

    total_files = sum(len(files) for files in files_by_prefix.values())
    print(f"Found {total_files} files to process")

    for prefix, files in files_by_prefix.items():
        print(f"  - {prefix}: {len(files)} files")

    success, errors = move_files(files_by_prefix, source_dir)

    print("\nSummary:")
    print(f"  - Files processed: {total_files}")
    print(f"  - Files moved successfully: {success}")
    print(f"  - Errors: {errors}")


if __name__ == "__main__":
    main()
