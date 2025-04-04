#!/usr/bin/env python3

import os
import re
import subprocess
import sys


def find_lecture_dirs():
    """Find all lecture directories in order (matching pattern XX_*)."""
    dirs = []
    for item in os.listdir("."):
        if os.path.isdir(item) and re.match(r"\d{2}_", item):
            dirs.append(item)
    return sorted(dirs)


def combine_markdown_files(output_file: str = "course_book.md"):
    """Combine all README.md files into a single markdown file."""
    # Start with title page
    title_content = [
        "---",
        "title: Programming Languages Design Workshop",
        "author: Vincenzo Ciancia",
        "date: \\today",
        "---",
        "",
        "\\newpage",
        "",
    ]
    content = title_content

    # Add the main README
    # with open("README.md", "r") as f:
    #     content.append(f.read())

    # Add each lecture's README
    for dir_name in find_lecture_dirs():
        readme_path = os.path.join(dir_name, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as f:
                # Add a newpage for PDF
                content.append("\n\\newpage\n")

                # Read the content and strip out slide separators
                chapter_content = f.read()
                # Remove the HTML comment slide separators
                chapter_content = re.sub(r"<!--\s*slide\s*-->", "", chapter_content)

                content.append(chapter_content)

    # Write the combined content
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(content))


def build_book():
    """Build both PDF and HTML versions of the book."""
    # First combine all markdown files
    combine_markdown_files()

    # Convert to PDF using Pandoc
    print("Generating PDF...")
    try:
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
                # Font specifications for lambda support
                "-V",
                "mainfont=Times New Roman",
                "-V",
                "monofont=Courier New",
                # Make code font significantly smaller
                "-V",
                "monofontoptions:Scale=0.7",
                # Add syntax highlighting styling
                "-V",
                "colorlinks=true",
            ],
            check=True,
        )
        print("PDF generation successful!")
    except subprocess.CalledProcessError as e:
        print(f"Error generating PDF: {e}", file=sys.stderr)
        print("Continuing with HTML generation...", file=sys.stderr)

    # Convert to HTML using Pandoc
    print("Generating HTML...")
    try:
        # Try with newer --embed-resources flag first
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
                "--embed-resources",
            ],
            check=True,
        )
        print("HTML generation successful!")
    except subprocess.CalledProcessError:
        # Fall back to older --self-contained flag if --embed-resources fails
        try:
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
                ],
                check=True,
            )
            print("HTML generation successful with fallback method!")
        except subprocess.CalledProcessError as e:
            print(f"Error generating HTML: {e}", file=sys.stderr)

    print("Build complete! Generated files (if successful):")
    if os.path.exists("course_book.pdf"):
        print("- course_book.pdf")
    if os.path.exists("course_book.html"):
        print("- course_book.html")


if __name__ == "__main__":
    build_book()
