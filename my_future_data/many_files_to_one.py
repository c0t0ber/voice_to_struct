from pathlib import Path
import datetime
import os


def combine_markdown_files() -> None:
    """
    Combine all markdown files from data/struct directory into a single file.
    Files are sorted by creation time with most recent files first.
    Creation date is added to the header of each file.
    """
    # Get the current directory and struct directory
    struct_dir = Path("data") / "struct"

    # Get all markdown files
    markdown_files = list(struct_dir.glob("*.md"))

    # Sort files by creation time - most recent first
    markdown_files.sort(key=lambda x: os.path.getctime(x), reverse=True)

    # Create output file
    output_file = Path("combined.md")

    # Combine files
    with output_file.open("w", encoding="utf-8") as outfile:
        for file_path in markdown_files:
            # Get file creation time
            creation_time = os.path.getctime(file_path)
            creation_date = datetime.datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
            
            with file_path.open("r", encoding="utf-8") as infile:
                # Add filename and creation date as header
                filename = file_path.name
                outfile.write(f"# {filename} (Created: {creation_date})\n\n")

                # Write content
                content = infile.read()
                outfile.write(content)

                # Add separator between files
                outfile.write("\n\n---\n\n")

    print(f"Successfully combined {len(markdown_files)} markdown files into {output_file}")


if __name__ == "__main__":
    combine_markdown_files()
