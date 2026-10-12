from travis.rag.chunking import chunk_document
from travis.rag.models import ParsedDoc, Section


def make_doc(text: str) -> ParsedDoc:
    return ParsedDoc(
        path="notes/a.md", file_hash="h", file_type="md",
        sections=[Section(text=text, heading_path=["Intro"])],
    )


def test_children_link_to_parents_and_stay_small():
    text = "\n\n".join(
        " ".join(f"Sentence {i} about topic {p}." for i in range(40)) for p in range(6)
    )
    parents, children = chunk_document(make_doc(text))
    ids = {p.id for p in parents}
    assert parents and children
    assert all(c.parent_id in ids for c in children)
    assert all(len(c.text) <= 250 * 4 * 1.5 for c in children)


def test_ids_are_deterministic():
    d = make_doc("Alpha beta. Gamma delta.\n\nEpsilon zeta.")
    assert [c.id for c in chunk_document(d)[1]] == [c.id for c in chunk_document(d)[1]]