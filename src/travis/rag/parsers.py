import ast
import hashlib
import logging
import re
from pathlib import Path

import nbformat
import pymupdf4llm
from docx import Document as DocxDocument

from .models import ParsedDoc, Section

log = logging.getLogger(__name__)

HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
CODE_EXT = {".js", ".ts", ".java", ".c", ".cpp", ".h", ".go", ".rs", ".sql", ".sh", ".r", ".cs", ".kt"}
TEXT_EXT = {".md", ".txt", ".rst"}
SUPPORTED_EXT = {".pdf", ".docx", ".ipynb", ".py"} | CODE_EXT | TEXT_EXT


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def markdown_to_sections(
    md: str, page: int | None = None, stack: list[str] | None = None
) -> tuple[list[Section], list[str]]:
    """Split markdown at headings, tracking the heading path. Ignores '#' inside code fences."""
    stack = list(stack or [])
    sections: list[Section] = []
    buf: list[str] = []
    in_fence = False

    def flush() -> None:
        text = "\n".join(buf).strip()
        if text:
            sections.append(Section(text=text, heading_path=list(stack), page=page))
        buf.clear()

    for line in md.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        m = None if in_fence else HEADING.match(line)
        if m:
            flush()
            stack = stack[: len(m.group(1)) - 1] + [m.group(2)]
        else:
            buf.append(line)
    flush()
    return sections, stack


def parse_pdf(path: Path) -> list[Section]:
    pages = pymupdf4llm.to_markdown(str(path), page_chunks=True)
    sections: list[Section] = []
    stack: list[str] = []
    for i, page in enumerate(pages):
        md = page["text"]
        if len(md.strip()) < 20:
            log.warning("%s page %d has almost no text (scanned? needs OCR)", path.name, i + 1)
            continue
        secs, stack = markdown_to_sections(md, page=i + 1, stack=stack)
        sections.extend(secs)
    return sections


def parse_docx(path: Path) -> list[Section]:
    doc = DocxDocument(str(path))
    sections: list[Section] = []
    stack: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        text = "\n\n".join(buf).strip()
        if text:
            sections.append(Section(text=text, heading_path=list(stack)))
        buf.clear()

    for p in doc.paragraphs:
        style = p.style.name if p.style is not None and p.style.name else ""
        text = p.text.strip()
        if not text:
            continue
        if style.startswith("Heading"):
            flush()
            try:
                level = int(style.split()[-1])
            except ValueError:
                level = 1
            stack = stack[: level - 1] + [text]
        else:
            buf.append(text)
    flush()  # note: tables are skipped for now
    return sections


def parse_ipynb(path: Path) -> list[Section]:
    with path.open(encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)
    sections: list[Section] = []
    stack: list[str] = []
    for cell in nb.cells:
        src = cell.source.strip()
        if not src:
            continue
        if cell.cell_type == "markdown":
            secs, stack = markdown_to_sections(src, stack=stack)
            for s in secs:
                s.kind = "notebook_md"
            sections.extend(secs)
        elif cell.cell_type == "code":  # outputs are deliberately dropped
            sections.append(Section(text=src, heading_path=list(stack), kind="notebook_code"))
    return sections


def parse_python(path: Path) -> list[Section]:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [Section(text=text, heading_path=[path.name], kind="code")]
    lines = text.splitlines()
    covered = [False] * len(lines)
    sections: list[Section] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            first = node.decorator_list[0].lineno if node.decorator_list else node.lineno
            start, end = first - 1, node.end_lineno or first
            covered[start:end] = [True] * (end - start)
            sections.append(
                Section(text="\n".join(lines[start:end]), heading_path=[path.name, node.name], kind="code")
            )
    rest = "\n".join(line for line, c in zip(lines, covered) if not c).strip()
    if rest:
        sections.insert(0, Section(text=rest, heading_path=[path.name, "module level"], kind="code"))
    return sections


def parse_file(path: Path, root: Path | None = None) -> ParsedDoc:
    ext = path.suffix.lower()
    rel = path.relative_to(root).as_posix() if root else path.name
    if ext == ".pdf":
        secs = parse_pdf(path)
    elif ext == ".docx":
        secs = parse_docx(path)
    elif ext == ".ipynb":
        secs = parse_ipynb(path)
    elif ext == ".py":
        secs = parse_python(path)
    elif ext in CODE_EXT:
        text = path.read_text(encoding="utf-8", errors="replace")
        secs = [Section(text=text, heading_path=[path.name], kind="code")]
    elif ext in TEXT_EXT:
        secs, _ = markdown_to_sections(path.read_text(encoding="utf-8", errors="replace"))
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    return ParsedDoc(path=rel, file_hash=file_hash(path), file_type=ext.lstrip("."), sections=secs)