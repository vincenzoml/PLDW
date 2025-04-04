#!/usr/bin/env python3

import os
import re
import subprocess
import sys
import argparse
from datetime import date


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
    current_date = date.today().strftime("%B %d, %Y")
    title_content = [
        "---",
        "title: Programming Languages Design Workshop",
        "author: Vincenzo Ciancia",
        f"date: {current_date}",
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


def generate_slides_for_chapter(chapter_dir):
    """Generate slides for a single chapter."""
    # Extract chapter number and name
    chapter_num = chapter_dir.split("_", 1)[0] if "_" in chapter_dir else ""
    chapter_name = chapter_dir.split("_", 1)[1] if "_" in chapter_dir else chapter_dir

    # Set output files
    slides_markdown = f"Lecture_{chapter_num}_slides.md"
    slides_pdf = f"Lecture_{chapter_num}.pdf"

    # Read chapter content
    readme_path = os.path.join(chapter_dir, "README.md")
    if not os.path.exists(readme_path):
        print(f"  Skipping {chapter_dir}: README.md not found")
        return False

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split at slide markers
    slides = re.split(r"<!--\s*slide\s*-->", content)

    # Create slides markdown
    with open(slides_markdown, "w", encoding="utf-8") as f:
        # Get current date in a more readable format
        current_date = date.today().strftime("%B %d, %Y")

        # Write YAML header with quoted title
        f.write(
            f"""---
title: "Lecture {chapter_num}: {chapter_name}"
author: "Vincenzo Ciancia"
date: "{current_date}"
---

"""
        )

        # Add each slide
        slide_count = 0
        for i, slide in enumerate(slides):
            if i > 0:  # Skip first part (before first slide marker)
                slide_content = slide.strip()
                if slide_content:
                    if slide_count > 0:  # Don't add separator before first slide
                        f.write("\n---\n\n")
                    f.write(slide_content + "\n\n")
                    slide_count += 1

        print(f"  Created {slide_count} slides for chapter {chapter_num}")

    # Generate PDF with pandoc
    print(f"  Generating PDF: {slides_pdf}")
    try:
        subprocess.run(
            [
                "pandoc",
                slides_markdown,
                "-o",
                slides_pdf,
                "--from=markdown",
                "--to=beamer",
                "--pdf-engine=xelatex",
                "--variable=fontsize:10pt",
                "--variable=theme:metropolis",
                "--variable=colortheme:default",
                "--variable=aspectratio:169",
                "--highlight-style=tango",
                "-V",
                "monofont=Courier New",
                "-V",
                "monofontoptions:Scale=0.6",
            ],
            check=True,
        )
        print(f"  Successfully created PDF: {slides_pdf}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Error generating PDF for {chapter_dir}: {e}")
        return False


def build_slides_for_all_chapters():
    """Build slides for all chapters."""
    print("Generating slides for all chapters...")
    success_count = 0

    for dir_name in find_lecture_dirs():
        print(f"Processing {dir_name}...")
        if generate_slides_for_chapter(dir_name):
            success_count += 1

    print(f"Slides generation complete. Generated slides for {success_count} chapters.")


def main():
    """Parse command-line arguments and run the requested actions."""
    parser = argparse.ArgumentParser(description="Build course book and/or slides")
    parser.add_argument(
        "--slides", action="store_true", help="Generate slides for all chapters"
    )
    parser.add_argument(
        "--chapter",
        type=str,
        help="Generate slides for a specific chapter (e.g., '04')",
    )
    parser.add_argument("--book", action="store_true", help="Generate the course book")

    args = parser.parse_args()

    # Default to building the book if no args provided
    if not (args.slides or args.chapter or args.book):
        build_book()
        return

    # Process requested actions
    if args.book:
        build_book()

    if args.slides:
        build_slides_for_all_chapters()

    if args.chapter:
        chapter_dir = None
        for dir_name in find_lecture_dirs():
            if dir_name.startswith(args.chapter):
                chapter_dir = dir_name
                break

        if chapter_dir:
            generate_slides_for_chapter(chapter_dir)
        else:
            print(f"Chapter {args.chapter} not found.")


if __name__ == "__main__":
    main()
