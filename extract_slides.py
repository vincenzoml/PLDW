#!/usr/bin/env python3
import re, os

with open("04_Domains/README.md", "r") as f:
    content = f.read()
slides = re.split(r"<!--\s*slide\s*-->", content)
print(f"Found {len(slides)} slide sections")
with open("Lecture_04_slides.md", "w") as f:
    f.write(
        '---\ntitle: "Lecture 04: Domains"\nauthor: "Vincenzo Ciancia"\ndate: "\\today"\n---\n\n'
    )
    for i, slide in enumerate(slides):
        if i > 0:  # Skip first part
            slide_content = slide.strip()
            if slide_content:
                if i > 1:  # Don't add separator before first slide
                    f.write("\n---\n\n")
                f.write(slide_content + "\n\n")
print("Created slides markdown file: Lecture_04_slides.md")
print("Now you can generate the PDF with pandoc:")
print(
    "pandoc Lecture_04_slides.md -o Lecture_04.pdf --from=markdown --to=beamer --pdf-engine=xelatex"
)
