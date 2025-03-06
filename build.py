#!/usr/bin/env python3

import os
import re
import subprocess
from pathlib import Path
from typing import List


def find_lecture_dirs() -> List[str]:
    """Find all lecture directories in order (matching pattern XX_*)."""
    dirs = []
    for item in os.listdir("."):
        if os.path.isdir(item) and re.match(r"\d{2}_", item):
            dirs.append(item)
    return sorted(dirs)


def combine_markdown_files(output_file: str = "course_book.md"):
    """Combine all README.md files into a single markdown file."""
    # Start with the main README
    with open("README.md", "r") as f:
        content = [f.read()]

    # Add each lecture's README
    for dir_name in find_lecture_dirs():
        readme_path = os.path.join(dir_name, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, "r") as f:
                # Add a newpage for PDF
                content.append("\n\\newpage\n")
                content.append(f.read())

    # Write the combined content
    with open(output_file, "w") as f:
        f.write("\n".join(content))


def build_book():
    """Build both PDF and HTML versions of the book."""
    # First combine all markdown files
    combine_markdown_files()

    # Convert to PDF using Pandoc
    print("Generating PDF...")
    subprocess.run(
        [
            "pandoc",
            "course_book.md",
            "-o",
            "course_book.pdf",
            "--from=markdown+yaml_metadata_block+raw_html",
            "--pdf-engine=xelatex",
            "--toc",
            "--toc-depth=3",
            "--highlight-style=tango",
            "-V",
            "geometry:margin=1in",
            "-V",
            "mainfont:DejaVu Sans",
            "-V",
            "monofont:DejaVu Sans Mono",
        ]
    )

    # Convert to HTML using Pandoc
    print("Generating HTML...")
    subprocess.run(
        [
            "pandoc",
            "course_book.md",
            "-o",
            "course_book.html",
            "--from=markdown+yaml_metadata_block+raw_html",
            "--to=html5",
            "--toc",
            "--toc-depth=3",
            "--highlight-style=tango",
            "--standalone",
            "--self-contained",
        ]
    )

    print("Build complete! Generated:")
    print("- course_book.pdf")
    print("- course_book.html")


if __name__ == "__main__":
    build_book()
