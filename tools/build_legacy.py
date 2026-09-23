#!/usr/bin/env python3

import math
import shutil
import tempfile
import os
import re
import subprocess
import sys
import argparse
import time
from datetime import date
from pathlib import Path


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


def get_all_lecture_readmes():
    """Return a list of all lecture README.md file paths."""
    return [
        os.path.join(dir_name, "README.md")
        for dir_name in find_lecture_dirs()
        if os.path.exists(os.path.join(dir_name, "README.md"))
    ]


def build_book(force=False):
    """Build both PDF and HTML versions of the book."""
    # First combine all markdown files
    combine_markdown_files()

    pdf_file = "course_book.pdf"
    # Compute latest mtime among all lecture README.md files
    lecture_readmes = get_all_lecture_readmes()
    if not lecture_readmes:
        print("[BOOK] No lecture README.md files found, cannot generate PDF.")
        return
    latest_md_mtime = max(os.path.getmtime(f) for f in lecture_readmes)
    latest_md_file = max(lecture_readmes, key=lambda f: os.path.getmtime(f))
    regenerate_pdf = True
    if os.path.exists(pdf_file):
        pdf_mtime = os.path.getmtime(pdf_file)
        print(
            f"[BOOK] PDF: {pdf_file} mtime: {pdf_mtime} ({date.fromtimestamp(pdf_mtime)})"
        )
        print(
            f"[BOOK] Latest lecture README: {latest_md_file} mtime: {latest_md_mtime} ({date.fromtimestamp(latest_md_mtime)})"
        )
        if pdf_mtime > latest_md_mtime and not force:
            print(f"[BOOK] Decision: keep existing PDF (not regenerating)")
            regenerate_pdf = False
        else:
            print(f"[BOOK] Decision: regenerate PDF")
    else:
        print(f"[BOOK] PDF does not exist, will generate.")
        print(f"[BOOK] Decision: regenerate PDF")

    if regenerate_pdf:
        print("Generating PDF...")
        try:
            subprocess.run(
                [
                    "pandoc",
                    "course_book.md",
                    "-o",
                    pdf_file,
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



# Roughly how many rendered lines fit on one slide at the current type size.
# Slides estimated to be well past this are allowed to break across frames;
# everything else is shrunk, which is a no-op unless the content really does
# overflow.
# One place for the pandoc invocation, so the overflow check compiles exactly
# what the build produces.
PANDOC_SLIDE_ARGS = [
    "--from=markdown",
    "--slide-level=2",
    "--to=beamer",
    "--pdf-engine=xelatex",
    "--variable=fontsize:12pt",
    "--variable=theme:metropolis",
    "--variable=colortheme:default",
    "--variable=aspectratio:169",
    "--highlight-style=kate",
    "--include-in-header=slides_theme.tex",
]

SLIDE_LINE_BUDGET = 17
SLIDE_BREAK_THRESHOLD = 20  # measured: worst shrink 85%, vs 67% at any higher value
CHARS_PER_RENDERED_LINE = 95


def estimate_slide_lines(slide_content: str) -> float:
    """Estimate how many rendered lines a slide will occupy.

    Code lines map one to one; prose wraps; headings and fence delimiters cost
    roughly a line and a half each because of the space around them.
    """
    total = 0.0
    in_code = False
    for line in slide_content.split("\n"):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            total += 1.0
            continue
        if in_code:
            total += 1.0
        elif not line.strip():
            total += 0.4
        elif line.lstrip().startswith("#"):
            total += 1.8
        elif line.lstrip().startswith("!["):
            total += 9.0  # a figure takes roughly half the frame
        else:
            total += max(1.0, math.ceil(len(line) / CHARS_PER_RENDERED_LINE))
    return total


def slide_frame_options(slide_content: str) -> str:
    """Pick the beamer frame options that stop this slide from overflowing.

    Two mechanisms, and they cannot be combined. `shrink` scales the frame down
    until it fits, and costs nothing when the content already fits — so it is
    the default. But it is the wrong tool for a slide carrying far more than a
    screenful, which would end up unreadably small; that one is allowed to
    break across continuation frames instead.
    """
    # pandoc marks any slide holding a listing as `fragile`, and beamer never
    # breaks a fragile frame -- so allowframebreaks is useless there, however
    # long the slide is. Such a slide can only be scaled.
    has_code = "```" in slide_content
    if not has_code and estimate_slide_lines(slide_content) > SLIDE_BREAK_THRESHOLD:
        return "{.allowframebreaks}"
    return "{.shrink}"


def split_slide_blocks(slide_content: str):
    """Split a slide into paragraph-level chunks, keeping fenced code whole."""
    chunks, current, in_code = [], [], False
    for line in slide_content.split("\n"):
        fence = line.lstrip().startswith("```")
        if fence:
            in_code = not in_code
            current.append(line)
            if not in_code:  # closing fence ends the chunk
                chunks.append("\n".join(current))
                current = []
            continue
        if in_code:
            current.append(line)
        elif not line.strip():
            if current:
                chunks.append("\n".join(current))
                current = []
        else:
            current.append(line)
    if current:
        chunks.append("\n".join(current))
    return [c for c in chunks if c.strip()]


def split_oversized_slide(slide_content: str):
    """Break a slide that cannot possibly fit into a sequence of slides.

    beamer's own `allowframebreaks` is useless here: pandoc marks any slide
    containing a code listing as `fragile`, and a fragile frame is never
    broken. So the split has to happen before pandoc sees it, at paragraph
    boundaries, never inside a fenced block.
    """
    if estimate_slide_lines(slide_content) <= SLIDE_BREAK_THRESHOLD:
        return [slide_content]

    parts, current, budget = [], [], 0.0
    for chunk in split_slide_blocks(slide_content):
        cost = estimate_slide_lines(chunk)
        if current and budget + cost > SLIDE_LINE_BUDGET:
            parts.append("\n\n".join(current))
            current, budget = [], 0.0
        current.append(chunk)
        budget += cost
    if current:
        parts.append("\n\n".join(current))
    return parts


def normalize_slide_headings(slide_content: str) -> str:
    """Give a slide exactly one level-2 heading, so pandoc renders it as the
    frame title rather than as a block inside an untitled frame.

    The first heading of the slide (at any level) becomes the frame title;
    any further heading is pushed below level 2 so it stays in the body.
    A slide that starts without a heading gets an empty title.
    """
    opts = slide_frame_options(slide_content)
    lines = slide_content.split("\n")
    seen_title = False
    in_code = False
    out = []
    for line in lines:
        if line.lstrip().startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        # A "#" inside a fenced block is a comment in the listing, not a
        # heading: rewriting it would corrupt the code being shown.
        m = None if in_code else re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            text = m.group(2).rstrip()
            if not seen_title:
                out.append(f"## {text} {opts}")
                seen_title = True
            else:
                # Not a nested heading: pandoc would turn it into a beamer
                # block, and a block cannot be split across continuation
                # frames — which is how slides came to overflow. An emphasised
                # paragraph reads as a subheading and stays breakable.
                out.append(f"**{text}**")
                out.append("")  # keep it a paragraph of its own
        else:
            out.append(line)
    if not seen_title:
        out.insert(0, f"## {opts}")
    return "\n".join(out).strip()



LIST_ITEM = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)\S")


def _lazy_list_positions(lines):
    """Indices of list items that markdown will swallow into the text above.

    A list needs a blank line before it. Written as

        In functional programming, functions can be:
        - assigned to variables

    markdown reads the bullet as a continuation of the sentence, and the slide
    shows one run-on line with stray hyphens in it.

    A list item whose predecessor is itself part of the same list is fine,
    including when an earlier item wrapped over several lines -- so the scan
    walks back to the last blank line before deciding.
    """
    positions = []
    in_code = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or i == 0 or not LIST_ITEM.match(line):
            continue
        prev = lines[i - 1]
        if not prev.strip() or prev.lstrip().startswith(("#", "```", ">", "|")):
            continue
        # walk back to the start of this block: are we already inside a list?
        inside_list = False
        for j in range(i - 1, -1, -1):
            if not lines[j].strip():
                break
            if LIST_ITEM.match(lines[j]):
                inside_list = True
                break
        if not inside_list:
            positions.append(i)
    return positions


def find_lazy_lists(slide_content: str):
    """The offending lines, for reporting."""
    lines = slide_content.split("\n")
    return [lines[i - 1].strip()[:64] for i in _lazy_list_positions(lines)]


def repair_lazy_lists(slide_content: str) -> str:
    """Insert the blank line a list needs to be recognised as a list."""
    lines = slide_content.split("\n")
    positions = set(_lazy_list_positions(lines))
    out = []
    for i, line in enumerate(lines):
        if i in positions:
            out.append("")
        out.append(line)
    return "\n".join(out)


def frame_titles_by_tex_line(tex_path):
    """Map each line of a generated .tex to the frame title it falls inside."""
    titles = {}
    current = "(front matter)"
    with open(tex_path, encoding="utf-8", errors="ignore") as f:
        for n, line in enumerate(f, 1):
            m = re.search(r"\\begin\{frame\}(?:\[[^\]]*\])?\{(.*)$", line)
            if m:
                current = m.group(1).rstrip("}").strip() or "(untitled)"
            elif "\\frame{\\titlepage}" in line:
                current = "(title page)"
            titles[n] = current
    return titles


def measure_overflow(chapter_dirs=None):
    """Compile every deck and report what actually runs off the page.

    The density estimate is a guess; this is the measurement. LaTeX reports an
    Overfull \\vbox when content is taller than the slide and an Overfull
    \\hbox when a line is wider than the text column, and both are things the
    audience sees.
    """
    workdir = tempfile.mkdtemp(prefix="pldw-check-")
    results = []
    decks = [
        (d, f"Lecture_{d.split('_', 1)[0]}")
        for d in (chapter_dirs or find_lecture_dirs())
    ]
    if not chapter_dirs:
        decks += [(name, name) for name in LESSONS]
    for dir_name, stem in decks:
        md = f"{stem}_slides.md"
        if not os.path.exists(md):
            continue
        tex = os.path.join(workdir, f"{stem}.tex")
        try:
            subprocess.run(
                ["pandoc", md, "-o", tex, "-s"] + PANDOC_SLIDE_ARGS,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["xelatex", "-interaction=batchmode", os.path.basename(tex)],
                cwd=workdir,
                capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"  Could not measure {dir_name}: {e}")
            continue

        log = tex[:-4] + ".log"
        if not os.path.exists(log):
            continue
        titles = frame_titles_by_tex_line(tex)
        with open(log, encoding="utf-8", errors="ignore") as f:
            log_text = f.read()

        for kind, pattern in (
            ("too tall", r"Overfull \\vbox \(([0-9.]+)pt too high\) detected at line (\d+)"),
            ("too wide", r"Overfull \\hbox \(([0-9.]+)pt too wide\).*?lines (\d+)"),
        ):
            for m in re.finditer(pattern, log_text, flags=re.S):
                amount, line_no = float(m.group(1)), int(m.group(2))
                title = titles.get(line_no, "?")
                if title == "(title page)" or amount <= 2:
                    continue  # metropolis' own title page, and hairline slop
                results.append((dir_name, title, kind, amount))
    shutil.rmtree(workdir, ignore_errors=True)
    return results


def check_slides(verbose: bool = True):
    """Report everything that will look wrong on a slide, before it does.

    Three separate faults, because they have three separate causes: content
    that physically leaves the page, slides so crowded they only fit after
    being scaled down, and list items written inline in the source so markdown
    never turns them into a list.
    """
    crowded, inline_lists = [], []
    for dir_name in find_lecture_dirs():
        readme_path = os.path.join(dir_name, "README.md")
        if not os.path.exists(readme_path):
            continue
        with open(readme_path, "r", encoding="utf-8") as f:
            slides = re.split(r"<!--\s*slide\s*-->", f.read())
        for i, slide in enumerate(slides):
            if i == 0 or not slide.strip():
                continue
            slide = slide.strip()
            title = next(
                (
                    ln.lstrip("# ").strip()
                    for ln in slide.split("\n")
                    if ln.lstrip().startswith("#")
                ),
                slide.split("\n")[0][:40],
            )
            est = estimate_slide_lines(slide)
            if est > SLIDE_LINE_BUDGET:
                action = (
                    "split into separate slides"
                    if est > SLIDE_BREAK_THRESHOLD
                    else f"shrunk to about {SLIDE_LINE_BUDGET / est:.0%}"
                )
                crowded.append((dir_name, i, est, action, title))
            for hit in find_lazy_lists(slide):
                inline_lists.append((dir_name, i, title, hit))

    overflows = measure_overflow()

    if verbose:
        print("=" * 78)
        print("1. CONTENT THAT LEAVES THE PAGE  (measured by compiling)")
        print("=" * 78)
        if not overflows:
            print("None. Every slide fits, horizontally and vertically.\n")
        else:
            for dir_name, title, kind, amount in sorted(
                overflows, key=lambda r: -r[3]
            ):
                print(f"  {amount:7.1f}pt {kind:<9} {dir_name:<30} {title[:40]}")
            print()

        print("=" * 78)
        print(f"2. CROWDED SLIDES  (over the {SLIDE_LINE_BUDGET}-line budget)")
        print("=" * 78)
        if not crowded:
            print("None.\n")
        else:
            crowded.sort(key=lambda r: -r[2])
            print(f"  {'chapter':<30}{'slide':>6}{'lines':>7}  {'build does':<28}title")
            for dir_name, i, est, action, title in crowded:
                print(f"  {dir_name:<30}{i:>6}{est:>7.0f}  {action:<28}{title[:36]}")
            print()

        print("=" * 78)
        print("3. LISTS MISSING A BLANK LINE  (repaired in the build; fix the source)")
        print("=" * 78)
        if not inline_lists:
            print("None.")
        else:
            for dir_name, i, title, hit in inline_lists:
                print(f"  {dir_name:<30}{i:>4}  {title[:26]:<28}{hit}")

    return overflows, crowded, inline_lists


# A standalone figure on a slide that also carries text is laid out beside the
# text instead of above it, when the figure is not much wider than tall: stacked,
# the two together overflow and the whole slide gets shrunk, text included.
FIGURE_LINE = re.compile(r"^!\[[^\]]*\]\(([^)\s]+)\)(\{[^}]*\})?\s*$")
SIDE_BY_SIDE_MAX_ASPECT = 1.4


def image_aspect(path):
    """Width over height of an image file, or None if it cannot be read."""
    try:
        from PIL import Image  # optional: without it, figures stay stacked

        with Image.open(path) as im:
            return im.width / im.height
    except Exception:
        return None


def layout_figures(slide_md: str) -> str:
    """Put a lone, not-too-wide figure in a left column and the text on the right."""
    lines = slide_md.split("\n")
    figs = [i for i, ln in enumerate(lines) if FIGURE_LINE.match(ln)]
    if len(figs) != 1:
        return slide_md
    path = FIGURE_LINE.match(lines[figs[0]]).group(1)
    aspect = image_aspect(path)
    if aspect is None or aspect >= SIDE_BY_SIDE_MAX_ASPECT:
        return slide_md

    head, body = [], lines
    if body and body[0].startswith("## "):
        head, body = [body[0]], body[1:]
    i = figs[0] - len(head)

    # an italic paragraph right after the figure is its caption, and goes with it
    j = i + 1
    while j < len(body) and not body[j].strip():
        j += 1
    k = j
    while k < len(body) and body[k].strip():
        k += 1
    paragraph = body[j:k]
    is_caption = (
        paragraph
        and paragraph[0].lstrip().startswith("*")
        and not paragraph[0].lstrip().startswith("**")
        and paragraph[-1].rstrip().endswith("*")
    )
    caption = paragraph if is_caption else []
    rest = body[:i] + (body[k:] if is_caption else body[i + 1 :])

    text = "\n".join(rest).strip()
    if not text:
        return slide_md
    left = f"![]({path}){{width=100%}}"
    if caption:
        left += "\n\n" + "\n".join(caption)
    return "\n".join(head) + (
        "\n\n:::: {.columns}\n"
        '::: {.column width="44%"}\n'
        f"{left}\n"
        ":::\n"
        '::: {.column width="54%"}\n'
        f"{text}\n"
        ":::\n"
        "::::"
    )


def section_page(slide_md: str) -> str:
    """A slide that is only a heading becomes a section page, not an empty frame."""
    stripped = slide_md.strip()
    m = re.match(r"^##\s+(.*?)\s*(\{[^}]*\})?$", stripped)
    if m and "\n" not in stripped and m.group(1):
        return f"# {m.group(1)}"
    return slide_md


def chapter_slides(chapter_dir):
    """Turn a chapter README into (title, subtitle, slides) ready for pandoc.

    The title is the chapter's H1 (or the directory name). A first slide that
    only restates that H1 is dropped, and a short line under it becomes the
    subtitle, so the deck does not open with two title pages.
    """
    chapter_num = chapter_dir.split("_", 1)[0] if "_" in chapter_dir else ""
    chapter_name = chapter_dir.split("_", 1)[1] if "_" in chapter_dir else chapter_dir
    with open(os.path.join(chapter_dir, "README.md"), "r", encoding="utf-8") as f:
        content = f.read()
    slides = re.split(r"<!--\s*slide\s*-->", content)

    h1 = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
    title = (
        h1.group(1).strip()
        if h1
        else f"Lecture {chapter_num}: " + chapter_name.replace("_", " ")
    )
    subtitle = ""
    for i, slide in enumerate(slides):
        if i == 0 or not slide.strip():
            continue
        body = slide.strip()
        if h1 and body.split("\n", 1)[0].strip() == h1.group(0).strip():
            rest = body.split("\n", 1)[1].strip() if "\n" in body else ""
            lines = [ln for ln in rest.split("\n") if ln.strip()]
            if len(lines) <= 2 and "```" not in rest:
                subtitle = " ".join(ln.strip().strip("*_") for ln in lines)
                slides[i] = ""
            else:
                slides[i] = rest
        break

    out = []
    for i, slide in enumerate(slides):
        if i == 0:  # text before the first slide marker is not a slide
            continue
        slide_content = slide.strip()
        if not slide_content:
            continue
        slide_content = repair_lazy_lists(slide_content)
        # figures are referenced relative to the chapter, but the
        # intermediate markdown is compiled from the repository root
        slide_content = re.sub(
            r"\]\((?!https?://|/)([^)]+)\)",
            lambda m: f"]({chapter_dir}/{m.group(1)})"
            if os.path.exists(os.path.join(chapter_dir, m.group(1)))
            else m.group(0),
            slide_content,
        )
        parts = split_oversized_slide(slide_content)
        slide_title = next(
            (
                ln.lstrip("# ").strip()
                for ln in slide_content.split("\n")
                if ln.lstrip().startswith("#")
            ),
            "",
        )
        for k, part in enumerate(parts):
            if k > 0 and slide_title:
                # continuation slides carry the title forward
                part = f"### {slide_title} (continued)\n\n{part}"
            out.append(section_page(layout_figures(normalize_slide_headings(part))))
    return title, subtitle, out


def yaml_header(title, subtitle=""):
    current_date = date.today().strftime("%B %d, %Y")
    header = f'---\ntitle: "{title}"\n'
    if subtitle:
        header += f'subtitle: "{subtitle}"\n'
    return header + f'author: "Vincenzo Ciancia"\ndate: "{current_date}"\n---\n\n'


def compile_slides(slides_markdown, slides_pdf, sources, force=False):
    """Run pandoc unless the PDF is newer than every source it depends on."""
    if os.path.exists(slides_pdf) and not force:
        newest = max(os.path.getmtime(s) for s in sources)
        if os.path.getmtime(slides_pdf) > newest:
            print(f"  {slides_pdf} is up to date")
            return False
    print(f"  Generating PDF: {slides_pdf}")
    try:
        subprocess.run(
            ["pandoc", slides_markdown, "-o", slides_pdf] + PANDOC_SLIDE_ARGS,
            check=True,
        )
        print(f"  Successfully created PDF: {slides_pdf}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Error generating PDF {slides_pdf}: {e}")
        return False


def generate_slides_for_chapter(chapter_dir, force=False):
    """Generate the slide deck of a single chapter."""
    readme_path = os.path.join(chapter_dir, "README.md")
    if not os.path.exists(readme_path):
        print(f"  Skipping {chapter_dir}: README.md not found")
        return False
    chapter_num = chapter_dir.split("_", 1)[0] if "_" in chapter_dir else ""
    slides_markdown = f"Lecture_{chapter_num}_slides.md"
    slides_pdf = f"Lecture_{chapter_num}.pdf"

    title, subtitle, slides = chapter_slides(chapter_dir)
    with open(slides_markdown, "w", encoding="utf-8") as f:
        f.write(yaml_header(title, subtitle))
        f.write("\n\n".join(slides) + "\n")
    print(f"  Created {len(slides)} slides for chapter {chapter_num}")
    return compile_slides(slides_markdown, slides_pdf, [readme_path], force)


# A lesson is what is actually taught in one session: one or more chapters in
# a single deck, each chapter opening with a part divider. Chapters keep their
# own sources, so the concepts of each stay separate.
LESSONS = {
    "Lesson_01": {
        "title": "Lesson 1: Why Build a Language, and What One Is Made Of",
        "subtitle": "Programming Language Design Lab — University of Pisa",
        "chapters": ["00_Why_A_Language", "01_Introduction"],
    },
}


def build_lesson(name, force=False):
    """Assemble a lesson deck from its chapters, one part per chapter."""
    spec = LESSONS[name]
    slides_markdown = f"{name}_slides.md"
    slides_pdf = f"{name}.pdf"
    body = []
    for k, chapter_dir in enumerate(spec["chapters"]):
        title, subtitle, slides = chapter_slides(chapter_dir)
        part = chr(ord("A") + k)
        # strip "Chapter N:" so the divider reads as a part of this lesson
        plain = re.sub(r"^Chapter\s+\d+:\s*", "", title)
        body.append(f"# Part {part} — {plain}")
        body.extend(slides)
    with open(slides_markdown, "w", encoding="utf-8") as f:
        f.write(yaml_header(spec["title"], spec["subtitle"]))
        f.write("\n\n".join(body) + "\n")
    print(f"  Created {len(body)} slides for {name}")
    sources = [os.path.join(c, "README.md") for c in spec["chapters"]]
    return compile_slides(slides_markdown, slides_pdf, sources, force)


def build_slides_for_all_chapters(force=False):
    """Build slides for all chapters."""
    print("Generating slides for all chapters...")
    success_count = 0

    for dir_name in find_lecture_dirs():
        print(f"Processing {dir_name}...")
        if generate_slides_for_chapter(dir_name, force=force):
            success_count += 1

    for name in LESSONS:
        print(f"Processing {name}...")
        if build_lesson(name, force=force):
            success_count += 1

    print(f"Slides generation complete. Generated {success_count} decks.")


def get_files_to_watch():
    """Get all files that should be watched for changes."""
    files = []
    
    # Add all lecture README.md files
    files.extend(get_all_lecture_readmes())
    
    # Add main README if it exists
    if os.path.exists("README.md"):
        files.append("README.md")
    
    return files


def get_file_mtimes(files):
    """Get modification times for a list of files."""
    mtimes = {}
    for file in files:
        if os.path.exists(file):
            mtimes[file] = os.path.getmtime(file)
    return mtimes


def watch_mode(watch_slides=False, watch_book=False, watch_chapter=None, force=False):
    """Watch files for changes and rebuild when needed."""
    print("=" * 60)
    print("WATCH MODE STARTED")
    print("=" * 60)
    print("Watching for file changes. Press Ctrl+C to stop.")
    print()
    
    # Determine what to watch and build
    if watch_chapter:
        # Find the specific chapter directory
        chapter_dir = None
        for dir_name in find_lecture_dirs():
            if dir_name.startswith(watch_chapter):
                chapter_dir = dir_name
                break
        
        if not chapter_dir:
            print(f"Error: Chapter {watch_chapter} not found.")
            return
        
        readme_path = os.path.join(chapter_dir, "README.md")
        if not os.path.exists(readme_path):
            print(f"Error: {readme_path} not found.")
            return
        
        files_to_watch = [readme_path]
        print(f"Watching: {readme_path}")
        print(f"Will rebuild: Lecture_{watch_chapter} slides")
    else:
        files_to_watch = get_files_to_watch()
        print(f"Watching {len(files_to_watch)} files:")
        for f in files_to_watch:
            print(f"  - {f}")
        
        build_targets = []
        if watch_book:
            build_targets.append("book")
        if watch_slides:
            build_targets.append("all slides")
        if not build_targets:
            build_targets = ["book", "all slides"]
        
        print(f"Will rebuild: {', '.join(build_targets)}")
    
    print()
    print("Performing initial build...")
    print("-" * 60)
    
    # Initial build
    if watch_chapter:
        generate_slides_for_chapter(chapter_dir, force=force)
    else:
        if watch_book or not watch_slides:
            build_book(force=force)
        if watch_slides or not watch_book:
            build_slides_for_all_chapters(force=force)
    
    print("-" * 60)
    print("Initial build complete. Watching for changes...")
    print()
    
    # Track modification times
    last_mtimes = get_file_mtimes(files_to_watch)
    
    try:
        while True:
            time.sleep(1)  # Check every second
            
            current_mtimes = get_file_mtimes(files_to_watch)
            changed_files = []
            
            for file in files_to_watch:
                if file in current_mtimes and file in last_mtimes:
                    if current_mtimes[file] != last_mtimes[file]:
                        changed_files.append(file)
            
            if changed_files:
                print()
                print("=" * 60)
                print(f"DETECTED CHANGES at {time.strftime('%H:%M:%S')}")
                print("=" * 60)
                for f in changed_files:
                    print(f"  Changed: {f}")
                print()
                print("Rebuilding...")
                print("-" * 60)
                
                if watch_chapter:
                    generate_slides_for_chapter(chapter_dir, force=True)
                else:
                    if watch_book or not watch_slides:
                        build_book(force=True)
                    if watch_slides or not watch_book:
                        build_slides_for_all_chapters(force=True)
                
                print("-" * 60)
                print(f"Rebuild complete at {time.strftime('%H:%M:%S')}. Watching for changes...")
                print()
                
                # Update tracked times
                last_mtimes = get_file_mtimes(files_to_watch)
                
    except KeyboardInterrupt:
        print()
        print()
        print("=" * 60)
        print("WATCH MODE STOPPED")
        print("=" * 60)
        sys.exit(0)


def main():
    """Parse command-line arguments and run the requested actions."""
    parser = argparse.ArgumentParser(description="Build course book and slides")
    parser.add_argument(
        "--check",
        action="store_true",
        help="report slides at risk of overflowing, without building",
    )
    parser.add_argument(
        "--slides", action="store_true", help="Generate slides for all chapters"
    )
    parser.add_argument(
        "--chapter",
        type=str,
        help="Generate slides for a specific chapter (e.g., '04')",
    )
    parser.add_argument("--book", action="store_true", help="Generate the course book")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration even if output is newer than source",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch mode: automatically rebuild when files change",
    )

    args = parser.parse_args()

    # Overflow report: says what it would do, builds nothing
    if args.check:
        check_slides()
        return

    # Watch mode
    if args.watch:
        watch_mode(
            watch_slides=args.slides,
            watch_book=args.book,
            watch_chapter=args.chapter,
            force=args.force
        )
        return

    # By default, build both book and all slides if no specific options are given
    if not (args.slides or args.chapter or args.book):
        build_book(force=args.force)
        build_slides_for_all_chapters(force=args.force)
        return

    # Process requested actions
    if args.book:
        build_book(force=args.force)

    if args.slides:
        build_slides_for_all_chapters(force=args.force)

    if args.chapter:
        chapter_dir = None
        for dir_name in find_lecture_dirs():
            if dir_name.startswith(args.chapter):
                chapter_dir = dir_name
                break

        if chapter_dir:
            generate_slides_for_chapter(chapter_dir, force=args.force)
        else:
            print(f"Chapter {args.chapter} not found.")


if __name__ == "__main__":
    main()
