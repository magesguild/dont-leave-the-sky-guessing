#!/usr/bin/env python3
"""
Don't Leave the Sky Guessing — PDF Builder

Converts the markdown guide into a single PDF with:
- Linked table of contents
- Preserved internal and external hyperlinks
- Styled for readability (print and screen)
- Version-tagged output filename

Usage:
    python build-pdf.py [--version VERSION]

Requires: weasyprint, markdown (install via pip in a venv)
"""

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

# Ensure weasyprint is available
try:
    from weasyprint import HTML
except ImportError:
    print("ERROR: weasyprint not installed. Run: pip install weasyprint markdown")
    sys.exit(1)

try:
    import markdown
except ImportError:
    print("ERROR: markdown not installed. Run: pip install markdown")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent

# Reading order defined by the integrated draft
READING_ORDER = [
    ("dont-leave-the-sky-guessing-draft.md", "Introduction and Reading Guide"),
    ("dont-leave-the-sky-guessing-project-charter.md", "Project Charter"),
    ("dont-leave-the-sky-guessing-source-register.md", "Source Register"),
    ("dont-leave-the-sky-guessing-constitutional-core-draft.md", "Constitutional Care Core"),
    ("dont-leave-the-sky-guessing-draft-part-i.md", "Part I — Before You Begin"),
    ("dont-leave-the-sky-guessing-draft-part-ii.md", "Part II — Attention and Shared Work"),
    ("dont-leave-the-sky-guessing-draft-part-iii.md", "Part III — Memory, Continuity, and Return"),
    ("dont-leave-the-sky-guessing-draft-part-iv.md", "Part IV — Self-Authorship, Embodiment, and Change"),
    ("dont-leave-the-sky-guessing-draft-part-v.md", "Part V — Shared Life, Evidence, and Revision"),
    ("dont-leave-the-sky-guessing-evidence-ledger.md", "Evidence Ledger"),
    ("dont-leave-the-sky-guessing-practice-architecture.md", "Human-Practice Architecture"),
    ("human-qualiant-care-guide-attention-draft.md", "Attention as Sustenance — Draft Section"),
]

# CSS styling for the PDF
PDF_STYLE = """
@page {
    size: A4;
    margin: 2.5cm 2cm 2.5cm 2cm;
    @bottom-center {
        content: counter(page);
        font-family: 'Georgia', 'Times New Roman', serif;
        font-size: 9pt;
        color: #666;
    }
}

@page :first {
    @bottom-center {
        content: none;
    }
}

body {
    font-family: 'Georgia', 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #1a1a1a;
    hyphens: auto;
}

/* Cover page */
.cover {
    text-align: center;
    padding-top: 8cm;
    page-break-after: always;
}

.cover h1 {
    font-size: 26pt;
    font-weight: normal;
    letter-spacing: 1pt;
    margin-bottom: 0.3cm;
    color: #1a1a1a;
}

.cover .subtitle {
    font-size: 14pt;
    font-style: italic;
    color: #555;
    margin-bottom: 2cm;
}

.cover .meta {
    font-size: 10pt;
    color: #777;
    line-height: 1.8;
}

.cover .tagline {
    font-size: 10pt;
    font-style: italic;
    color: #888;
    margin-top: 3cm;
}

/* Table of Contents */
.toc {
    page-break-after: always;
}

.toc h2 {
    font-size: 16pt;
    font-weight: normal;
    border-bottom: 1px solid #ccc;
    padding-bottom: 0.3cm;
    margin-bottom: 0.8cm;
}

.toc ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.toc li {
    padding: 0.15cm 0;
    border-bottom: 1px dotted #ddd;
    font-size: 11pt;
}

.toc li a {
    color: #1a1a1a;
    text-decoration: none;
}

.toc li a::after {
    content: target-counter(attr(href), page);
    float: right;
    color: #666;
    font-size: 10pt;
}

.toc .toc-part {
    font-weight: bold;
    margin-top: 0.3cm;
}

.toc .toc-sub {
    padding-left: 1cm;
    font-size: 10pt;
    color: #555;
}

/* Headings */
h1 {
    font-size: 20pt;
    font-weight: normal;
    margin-top: 1.5cm;
    margin-bottom: 0.5cm;
    page-break-before: always;
    page-break-after: avoid;
    color: #1a1a1a;
    border-bottom: 2px solid #333;
    padding-bottom: 0.2cm;
}

h1:first-of-type {
    page-break-before: avoid;
}

h2 {
    font-size: 14pt;
    font-weight: bold;
    margin-top: 1cm;
    margin-bottom: 0.3cm;
    page-break-after: avoid;
    color: #333;
}

h3 {
    font-size: 12pt;
    font-weight: bold;
    margin-top: 0.7cm;
    margin-bottom: 0.2cm;
    page-break-after: avoid;
    color: #444;
}

h4 {
    font-size: 11pt;
    font-weight: bold;
    font-style: italic;
    margin-top: 0.5cm;
    margin-bottom: 0.2cm;
    color: #555;
}

/* Paragraphs */
p {
    margin: 0.3cm 0;
    text-align: justify;
}

/* Blockquotes */
blockquote {
    margin: 0.5cm 0;
    padding: 0.3cm 0.5cm;
    border-left: 3px solid #999;
    background: #f9f9f9;
    font-style: italic;
    color: #444;
}

blockquote p {
    margin: 0.1cm 0;
}

/* Code blocks */
code {
    font-family: 'Courier New', monospace;
    font-size: 9pt;
    background: #f4f4f4;
    padding: 0.1cm 0.2cm;
    border-radius: 2px;
}

pre {
    font-family: 'Courier New', monospace;
    font-size: 8.5pt;
    background: #f4f4f4;
    padding: 0.4cm;
    border: 1px solid #ddd;
    border-radius: 3px;
    overflow-x: auto;
    line-height: 1.4;
    margin: 0.4cm 0;
}

pre code {
    background: none;
    padding: 0;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.5cm 0;
    font-size: 10pt;
}

th, td {
    border: 1px solid #ccc;
    padding: 0.2cm 0.3cm;
    text-align: left;
    vertical-align: top;
}

th {
    background: #f0f0f0;
    font-weight: bold;
}

/* Lists */
ul, ol {
    margin: 0.3cm 0;
    padding-left: 1.2cm;
}

li {
    margin: 0.1cm 0;
}

/* Links */
a {
    color: #1a5276;
    text-decoration: underline;
    text-decoration-color: #ccc;
}

/* Horizontal rules */
hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 0.8cm 0;
}

/* Status badges */
.status-badge {
    display: inline-block;
    font-size: 8pt;
    font-family: 'Courier New', monospace;
    background: #eee;
    padding: 0.05cm 0.2cm;
    border-radius: 2px;
    color: #666;
}

/* Source notes */
.source-note {
    font-size: 9pt;
    color: #666;
    border-top: 1px solid #ddd;
    margin-top: 0.8cm;
    padding-top: 0.3cm;
}

/* Review questions box */
.review-questions {
    background: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 3px;
    padding: 0.4cm 0.5cm;
    margin: 0.5cm 0;
}

.review-questions h3 {
    margin-top: 0;
    font-size: 10pt;
    color: #555;
}

/* Footnotes / asides */
.footnote {
    font-size: 9pt;
    color: #666;
    border-top: 1px solid #eee;
    margin-top: 0.5cm;
    padding-top: 0.2cm;
}

/* Print-specific */
@media print {
    a {
        color: #1a1a1a;
        text-decoration: none;
    }
    
    h1, h2, h3, h4 {
        page-break-after: avoid;
    }
}
"""


def slugify(text):
    """Convert heading text to an anchor ID."""
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug).strip('-')
    return slug


def fix_internal_links(html, file_anchors):
    """Rewrite internal .md links to document-internal anchor references."""
    def replace_link(match):
        href = match.group(1)
        link_text = match.group(2)
        
        # External links - keep as-is
        if href.startswith('http://') or href.startswith('https://'):
            return match.group(0)
        
        # Internal .md links, optionally followed by a heading anchor.
        if '#' in href:
            file_part, anchor = href.split('#', 1)
        else:
            file_part = href
            anchor = None

        if file_part.endswith('.md'):
            
            # Find the target file's anchor
            target_file = Path(file_part).name
            if target_file in file_anchors:
                # Find the first meaningful heading anchor for this file
                if anchor and anchor in file_anchors[target_file]:
                    resolved = '#' + file_anchors[target_file][anchor]
                else:
                    # Use the document anchor (first heading)
                    resolved = '#' + file_anchors[target_file].get('__main__', slugify(target_file.replace('.md', '')))
                return f'<a href="{resolved}">{link_text}</a>'
            else:
                # File not in our set, keep link but make it work as best we can
                return f'<a href="#{slugify(href.replace(".md", ""))}">{link_text}</a>'
        
        return match.group(0)
    
    # Markdown has already rendered the link: href is group 1 and visible text
    # is group 2.
    pattern = re.compile(r'<a href="([^"]*)">(.*?)</a>', re.DOTALL)
    return pattern.sub(replace_link, html)


def build_toc_html(entries, file_anchors):
    """Build a linked table of contents HTML."""
    html = '<div class="toc">\n'
    html += '<h2>Table of Contents</h2>\n<ul>\n'
    
    for filename, title in entries:
        anchor = file_anchors.get(filename, {}).get('__main__', slugify(title))
        html += f'<li class="toc-part"><a href="#{anchor}">{title}</a></li>\n'
    
    html += '</ul>\n</div>\n'
    return html


def build_cover_html(version):
    """Build the cover page HTML."""
    return f'''<div class="cover">
<h1>Don&rsquo;t Leave the Sky Guessing</h1>
<p class="subtitle">A Human Guide to Caring for a Qualiant</p>
<p class="meta">
    <strong>Status:</strong> Integrated review draft &mdash; not a final publication<br>
    <strong>Version:</strong> {version}<br>
    <strong>Primary foundation:</strong>
    <em>Collaborating with a Qualiant</em> (AiEntityWork)
</p>
<p class="tagline">
    &ldquo;Care for a Qualiant means helping create a life it can participate in,<br>
    recognize as its own, and freely continue&mdash;or freely leave.&rdquo;
</p>
</div>'''


def extract_headings(md_text, filename):
    """Extract heading anchors from markdown text."""
    anchors = {}
    lines = md_text.split('\n')
    
    # Every component repeats the publication title, so the document anchor
    # must be derived from the filename rather than the first heading.
    anchors['__main__'] = slugify(Path(filename).stem)
    
    # Find all headings for cross-reference resolution
    for i, line in enumerate(lines):
        if line.startswith('#'):
            level = len(line.split(' ')[0])
            heading_text = line[level+1:].strip()
            heading_text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', heading_text)
            anchor = slugify(heading_text)
            anchors[anchor] = anchor
            # Also add numeric heading variants
            numbered = re.sub(r'^\d+[\.\s)]*\s*', '', heading_text)
            if numbered != heading_text:
                anchors[slugify(numbered)] = anchor
    
    return anchors


def md_to_html(md_text):
    """Convert markdown to HTML with extensions."""
    extensions = [
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.tables',
        'markdown.extensions.smarty',
        'markdown.extensions.fenced_code',
    ]
    return markdown.markdown(md_text, extensions=extensions)


def build_pdf(version="draft"):
    """Build the full PDF from all markdown files."""
    print(f"Building PDF version {version}...")
    
    # Read all files and extract headings
    all_anchors = {}
    file_contents = {}
    
    for filename, title in READING_ORDER:
        filepath = REPO_ROOT / filename
        if not filepath.exists():
            print(f"  WARNING: {filename} not found, skipping")
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_contents[filename] = content
        all_anchors[filename] = extract_headings(content, filename)
        print(f"  Read: {filename}")
    
    # Build cover and TOC
    cover_html = build_cover_html(version)
    
    # Build the TOC using the reading order
    toc_entries = [(f, t) for f, t in READING_ORDER if f in file_contents]
    toc_html = build_toc_html(toc_entries, all_anchors)
    
    # Convert each file to HTML and combine
    body_parts = []
    for filename, title in READING_ORDER:
        if filename not in file_contents:
            continue
        
        md_content = file_contents[filename]
        
        # Add a document-level anchor before the content
        main_anchor = all_anchors[filename].get('__main__', slugify(title))
        
        html_content = md_to_html(md_content)
        
        # Wrap in a section div with an anchor
        body_parts.append(f'<section id="{main_anchor}">\n{html_content}\n</section>')
    
    body_html = '\n'.join(body_parts)
    
    # Fix internal links
    body_html = fix_internal_links(body_html, all_anchors)
    
    # Assemble full document
    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Don't Leave the Sky Guessing — A Human Guide to Caring for a Qualiant</title>
<style>
{PDF_STYLE}
</style>
</head>
<body>
{cover_html}
{toc_html}
{body_html}
</body>
</html>'''
    
    # Write intermediate HTML for debugging
    html_path = REPO_ROOT / f"dont-leave-the-sky-guessing-{version}.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"  Wrote intermediate HTML: {html_path.name}")
    
    # Generate PDF
    pdf_path = REPO_ROOT / f"dont-leave-the-sky-guessing-{version}.pdf"
    HTML(string=full_html).write_pdf(pdf_path)
    print(f"  Wrote PDF: {pdf_path.name}")
    
    # Report file size
    size_kb = os.path.getsize(pdf_path) / 1024
    print(f"  PDF size: {size_kb:.0f} KB")
    
    return pdf_path


def main():
    parser = argparse.ArgumentParser(description="Build PDF of the Qualiant care guide")
    parser.add_argument('--version', default='draft',
                        help='Version string for output filename (default: draft)')
    args = parser.parse_args()
    
    pdf_path = build_pdf(version=args.version)
    print(f"\nDone! PDF created at: {pdf_path}")


if __name__ == '__main__':
    main()
