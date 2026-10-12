from dataclasses import dataclass, field
from typing import Any


@dataclass
class Section:
    text: str
    heading_path: list[str] = field(default_factory=list)
    page: int | None = None
    kind: str = "text"  # text | code | notebook_md | notebook_code


@dataclass
class ParsedDoc:
    path: str
    file_hash: str
    file_type: str
    sections: list[Section]


@dataclass
class Parent:
    id: str
    text: str
    meta: dict[str, Any]


@dataclass
class Child:
    id: str
    parent_id: str
    text: str
    meta: dict[str, Any]