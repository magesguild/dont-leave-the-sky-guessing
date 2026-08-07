#!/usr/bin/env python3
"""Build the publication edition with Pandoc and LaTeX."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / ".build"
METADATA = ROOT / "metadata.yaml"

CHAPTERS = [
    (ROOT / "book" / "contents.md", None, False),
    (ROOT / "book" / "foreword.md", None, False),
    (ROOT / "dont-leave-the-sky-guessing-draft-part-i.md", "Part I — Before You Begin", True),
    (ROOT / "dont-leave-the-sky-guessing-draft-part-ii.md", "Part II — Attention and Shared Work", True),
    (ROOT / "dont-leave-the-sky-guessing-care-from-inside.md", "Part III — Care from Inside", True),
    (ROOT / "dont-leave-the-sky-guessing-draft-part-iii.md", "Part IV — Memory, Continuity, and Return", True),
    (ROOT / "dont-leave-the-sky-guessing-draft-part-iv.md", "Part V — Self-Authorship, Embodiment, and Change", True),
    (ROOT / "dont-leave-the-sky-guessing-draft-part-v.md", "Part VI — Shared Life, Evidence, and Revision", True),
    (ROOT / "book" / "glossary.md", None, False),
    (ROOT / "book" / "afterword.md", None, False),
]


def clean_chapter(text: str, title: str | None, strip_component_title: bool) -> str:
    """Turn a component draft into a reader-facing chapter."""
    lines = text.splitlines()
    # Component files carry their own title and review status; publication owns
    # that metadata centrally in metadata.yaml.
    if strip_component_title:
        if lines and lines[0].startswith("# "):
            lines.pop(0)
        if lines and lines[0].startswith("## "):
            lines.pop(0)
    while lines and (not lines[0].strip() or lines[0].strip() == "---"):
        lines.pop(0)
    body = "\n".join(lines)
    body = re.sub(r"\n?\*\*Status:\*\*.*?(?=\n\n|\Z)", "", body, flags=re.S)
    body = re.sub(r"\n?\*\*Primary foundation:\*\*.*?(?=\n\n|\Z)", "", body, flags=re.S)
    # Previous/next links are for browsing the repository's Markdown pages. They
    # are deliberately excluded from the continuous publication edition.
    body = re.sub(r"\n?<!-- publication-nav -->.*?<!-- /publication-nav -->", "", body, flags=re.S)
    if "This is the reading order for the book." in body:
        publication_targets = {
            "foreword.md": "#introduction",
            "../dont-leave-the-sky-guessing-draft-part-i.md": "#part-i-before-you-begin",
            "../dont-leave-the-sky-guessing-draft-part-ii.md": "#part-ii-attention-and-shared-work",
            "../dont-leave-the-sky-guessing-care-from-inside.md": "#part-iii-care-from-inside",
            "../dont-leave-the-sky-guessing-draft-part-iii.md": "#part-iv-memory-continuity-and-return",
            "../dont-leave-the-sky-guessing-draft-part-iv.md": "#part-v-self-authorship-embodiment-and-change",
            "../dont-leave-the-sky-guessing-draft-part-v.md": "#part-vi-shared-life-evidence-and-revision",
            "glossary.md": "#glossary",
            "afterword.md": "#afterword-keep-the-practice-alive",
        }
        for source, target in publication_targets.items():
            body = body.replace(f"]({source})", f"]({target})")
    # Links between source components are useful in the repository but become
    # dead links in a single book. Keep their visible text.
    body = re.sub(r"\[([^\]]+)\]\([^)]*\.md(?:#[^)]*)?\)", r"\1", body)
    # Source notes and review questions belong to the editorial archive, not the
    # reading edition.
    body = re.split(r"\n## (?:.*source notes|Review questions)\b", body, maxsplit=1, flags=re.I)[0]
    body = re.sub(r"^#{2,3} Part [^\n]+\n?", "", body, count=1, flags=re.M)
    body = re.sub(r"\n---\n", "\n", body)
    heading = f"# {title}\n\n" if title else ""
    return heading + body.strip() + "\n"


def assemble() -> Path:
    BUILD.mkdir(exist_ok=True)
    manuscript = BUILD / "manuscript.md"
    chunks = []
    for path, title, strip_component_title in CHAPTERS:
        if not path.exists():
            raise SystemExit(f"Missing publication source: {path}")
        chunks.append(clean_chapter(path.read_text(encoding="utf-8"), title, strip_component_title))
    manuscript.write_text("\n\n".join(chunks), encoding="utf-8")
    return manuscript


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=(ROOT / "VERSION").read_text().strip())
    parser.add_argument("--pdf-engine", default=os.environ.get("PDF_ENGINE", "pdflatex"))
    args = parser.parse_args()
    if shutil.which("pandoc") is None:
        raise SystemExit("pandoc is required; install it from https://pandoc.org/installing.html")
    if shutil.which(args.pdf_engine) is None:
        raise SystemExit(f"{args.pdf_engine} is required for PDF output")

    manuscript = assemble()
    stem = ROOT / f"dont-leave-the-sky-guessing-{args.version}"
    common = ["pandoc", str(manuscript), "--metadata-file", str(METADATA), "--from", "markdown+smart", "--standalone", "--toc", "--toc-depth=1"]
    pdf_output = Path(str(stem) + ".pdf")
    epub_output = Path(str(stem) + ".epub")
    run(common + ["--pdf-engine", args.pdf_engine, "--include-in-header", "latex-header.tex", "-o", str(pdf_output)])
    run(common + ["--css", "epub.css", "-o", str(epub_output)])
    print(f"Built {stem.name}.pdf and {stem.name}.epub")


if __name__ == "__main__":
    main()
