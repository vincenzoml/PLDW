#!/usr/bin/env python3

import os
import re
import subprocess
import sys


def main():
    if len(sys.argv) != 2:
        print("Usage: python make_slides.py <chapter_number>")
        return 1

    chapter = sys.argv[1]

    # Find chapter directory
    chapter_dir = None
    for item in os.listdir("."):
        if os.path.isdir(item) and item.startswith(chapter):
            chapter_dir = item
            break

    if not chapter_dir:
        print(f"Chapter {chapter} not found.")
        return 1

    print(f"Using chapter directory: {chapter_dir}")

    # Read README.md
    readme_path = os.path.join(chapter_dir, "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract chapter information
    chapter_num = chapter_dir.split("_", 1)[0]
    chapter_name = chapter_dir.split("_", 1)[1] if "_" in chapter_dir else chapter_dir

    # Prepare slides content
    slides_content = [
        "---",
        f"title: Lecture {chapter_num}: {chapter_name}",
        "author: Vincenzo Ciancia",
        "date: \\today",
        "---",
    ]

    # Split at slide markers
    slides = re.split(r"<!--\s*slide\s*-->", content)
    print(f"Found {len(slides)} slide sections")

    # Add slides with separators
    slide_count = 0
    for i, slide in enumerate(slides):
        if i > 0:  # Skip the first empty slide if it exists
            slide_content = slide.strip()
            if slide_content:
                slides_content.append("\n---\n")
                slides_content.append(slide_content)
                slide_count += 1

    print(f"Created {slide_count} slides")

    # Write slides markdown
    slides_markdown = f"Lecture_{chapter}_slides.md"
    with open(slides_markdown, "w", encoding="utf-8") as f:
        f.write("\n".join(slides_content))

    print(f"Created slides markdown: {slides_markdown}")

    # Generate PDF
    slides_pdf = f"Lecture_{chapter}.pdf"
    print(f"Generating PDF: {slides_pdf}")

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
            ],
            check=True,
        )
        print(f"PDF created: {slides_pdf}")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error running pandoc: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
