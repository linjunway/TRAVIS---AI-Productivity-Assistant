import hashlib
import re
import uuid
from pathlib import PurePosixPath

from .config import settings
from .models import Child, Parent, ParsedDoc

NS = uuid.UUID("6f1c0c1e-5a52-4d6e-9d46-0d2a8f6a1b11")
CODE_KINDS = {"code", "notebook_code"}
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")


def approx_tokens(s: str) -> int:
    return max(1, len(s) // 4)  # rough heuristic; swap for a real tokenizer later


def _h(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:12]


def _id(*parts: str) -> str:
    return str(uuid.uuid5(NS, "|".join(parts)))


def _hard_split(u: str, max_tokens: int) -> list[str]:
    if approx_tokens(u) <= max_tokens:
        return [u]
    size = max_tokens * 4
    return [u[i : i + size] for i in range(0, len(u), size)]


def _pack(units: list[str], max_tokens: int, overlap: int, sep: str) -> list[str]:
    chunks: list[str] = []
    cur: list[str] = []
    cur_tok = 0
    for u in units:
        t = approx_tokens(u)
        if cur and cur_tok + t > max_tokens:
            chunks.append(sep.join(cur))
            keep: list[str] = []
            kt = 0
            for prev in reversed(cur):
                pt = approx_tokens(prev)
                if kt + pt > overlap:
                    break
                keep.insert(0, prev)
                kt += pt
            cur, cur_tok = keep, kt
        cur.append(u)
        cur_tok += t
    if cur:
        chunks.append(sep.join(cur))
    return chunks


def chunk_document(doc: ParsedDoc) -> tuple[list[Parent], list[Child]]:
    parents: list[Parent] = []
    children: list[Child] = []
    for sec in doc.sections:
        is_code = sec.kind in CODE_KINDS
        raw = sec.text.split("\n") if is_code else re.split(r"\n\s*\n", sec.text)
        if not is_code:
            raw = [u for u in raw if u.strip()]
        units = [piece for u in raw for piece in _hard_split(u, settings.parent_max_tokens)]

        meta = {
            "source_path": doc.path,
            "file_type": doc.file_type,
            "heading_path": sec.heading_path,
            "page": sec.page,
            "kind": sec.kind,
            "file_hash": doc.file_hash,
        }
        for ptext in _pack(units, settings.parent_max_tokens, 0, "\n" if is_code else "\n\n"):
            pid = _id(doc.path, str(len(parents)), _h(ptext))
            parents.append(Parent(id=pid, text=ptext, meta=meta))

            cu = ptext.split("\n") if is_code else SENT.split(ptext.replace("\n", " "))
            cu = [piece for u in cu for piece in _hard_split(u, settings.child_max_tokens)]
            for ctext in _pack(
                cu, settings.child_max_tokens, settings.child_overlap_tokens, "\n" if is_code else " "
            ):
                cid = _id(pid, str(len(children)), _h(ctext))
                children.append(
                    Child(id=cid, parent_id=pid, text=ctext, meta={**meta, "child_index": len(children)})
                )
    return parents, children


def embed_text(child: Child) -> str:
    """Text actually embedded: file name + heading path give each chunk its context."""
    crumbs = [PurePosixPath(child.meta["source_path"]).name, *child.meta["heading_path"]]
    return f"{' > '.join(crumbs)}\n{child.text}"