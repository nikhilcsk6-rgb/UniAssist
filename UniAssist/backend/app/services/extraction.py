"""Extract text per page/section from PDF, DOCX and TXT files."""
import pymupdf
import docx


def extract_pages(path, file_type):
    """Return list of (page_number, text). DOCX/TXT have no real pages, so they are
    split into ~3000-character 'sections' numbered from 1 for citation purposes."""
    if file_type == "pdf":
        with pymupdf.open(path) as pdf:
            return [(i + 1, p.get_text("text")) for i, p in enumerate(pdf)]
    if file_type == "docx":
        d = docx.Document(path)
        text = "\n".join(p.text for p in d.paragraphs)
        for t in d.tables:
            for row in t.rows:
                text += "\n" + " | ".join(c.text for c in row.cells)
    else:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    return _sections(text)


def _sections(text, size=3000):
    paras, sections, cur = text.split("\n"), [], ""
    for p in paras:
        if len(cur) + len(p) > size and cur:
            sections.append(cur)
            cur = ""
        cur += p + "\n"
    if cur.strip():
        sections.append(cur)
    return [(i + 1, s) for i, s in enumerate(sections)]
