import argparse
from pathlib import Path

from .chunking import chunk_document
from .parsers import parse_file


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    p = Path(ap.parse_args().path)
    doc = parse_file(p, root=p.parent)
    parents, children = chunk_document(doc)
    print(f"{doc.path}: {len(doc.sections)} sections -> {len(parents)} parents, {len(children)} children")
    for c in children[:5]:
        print("---", c.meta["heading_path"], "page", c.meta["page"])
        print(c.text[:300])


if __name__ == "__main__":
    main()