"""Offsets always refer to the preserved parent, never to normalized search text."""

import re

import tiktoken

ENC = tiktoken.get_encoding("cl100k_base")


def normalize(text: str) -> str:
    return " ".join(text.split())


def tokens(text: str) -> int:
    return len(ENC.encode(text))


def split_spans(text: str, strategy="structure", target=280):
    if tokens(text) <= target:
        return [(0, len(text))]
    if strategy == "fixed":
        # Character spans aligned to words; count actual tokens, no UTF-8 slicing.
        boundaries = [m.end() for m in re.finditer(r"\S+\s*", text)]
    elif strategy == "recursive":
        boundaries = [m.end() for m in re.finditer(r"\n\s*\n|(?<=[.!?])\s+", text)]
    else:
        boundaries = [m.end() for m in re.finditer(r"(?<=[.!?])\s+|\n\s*\n", text)]
    boundaries = sorted(set(boundaries + [len(text)]))
    spans, start, last = [], 0, 0
    for end in boundaries:
        if tokens(text[start:end]) > target and last > start:
            spans.append((start, last))
            start = last
        if tokens(text[start:end]) > target * 1.3:
            # A single unusually long sentence/paragraph must still be bounded.
            for m in re.finditer(r"\S+\s*", text[start:end]):
                cut = start + m.end()
                if tokens(text[last:cut]) > target and cut > last:
                    spans.append((last, cut))
                    last = cut
            start = last
        last = end
    if start < len(text):
        spans.append((start, len(text)))
    return spans


def roman(value: str) -> int:
    vals = dict(I=1, V=5, X=10, L=50, C=100, D=500, M=1000)
    result, prev = 0, 0
    for ch in reversed(value):
        n = vals[ch]
        result += -n if n < prev else n
        prev = max(n, prev)
    return result


def strip_gutenberg(text):
    match = re.search(r"\*\*\* START OF .*?\*\*\*(.*?)\*\*\* END OF", text, re.S)
    if not match:
        raise ValueError("Missing Gutenberg boundaries")
    return match[1]


def parse_text(work, text):
    body = strip_gutenberg(text)
    if work == "meditations":
        body = body[body.index("THE FIRST BOOK") :]
        body = body.split("\nAPPENDIX")[0]
        books = list(re.finditer(r"(?m)^THE ([A-Z]+) BOOK\s*$", body))
        ordinal = "FIRST SECOND THIRD FOURTH FIFTH SIXTH SEVENTH EIGHTH NINTH TENTH ELEVENTH TWELFTH".split()
        units = []
        for i, b in enumerate(books):
            book = ordinal.index(b[1]) + 1
            segment = body[b.end() : books[i + 1].start() if i + 1 < len(books) else len(body)]
            sections = list(re.finditer(r"(?m)^([IVXLCDM]+)\.\s+", segment))
            for j, s in enumerate(sections):
                end = sections[j + 1].start() if j + 1 < len(sections) else len(segment)
                units.append(
                    (
                        f"{book}.{s[1]}",
                        segment[s.end() : end].strip(),
                        {
                            "book_number": book,
                            "section_number": roman(s[1]),
                            "reference": f"Book {book}, section {s[1]} (Casaubon numbering)",
                        },
                    )
                )
        if len(books) != 12 or len(units) < 400:
            raise ValueError("Meditations structure changed")
        return units
    marker = "\nTHE ENCHEIRIDION, OR MANUAL."
    if work == "enchiridion":
        segment = body.split(marker)[-1]
        sections = list(re.finditer(r"(?m)^([IVXLCDM]+)\.\s*$", segment))
        units = []
        for j, s in enumerate(sections):
            end = sections[j + 1].start() if j + 1 < len(sections) else len(segment)
            units.append(
                (s[1], segment[s.end() : end].strip(), {"section_number": roman(s[1]), "reference": f"Section {s[1]}"})
            )
        if len(units) != 52:
            raise ValueError(f"Expected 52 edition-specific sections, got {len(units)}")
        return units
    if work == "discourses":
        segment = body.split("\nA SELECTION FROM THE DISCOURSES OF EPICTETUS.")[-1].split(marker)[0]
        headings = list(re.finditer(r"(?m)^([A-Z][A-Z\s,?;\x27’()\-]+)\.—", segment))
        if len(headings) < 20:
            raise ValueError("Discourses headings not found")
        # Edition has named selections, not reliable original book/chapter numbers.
        return [
            (
                f"heading-{i + 1}",
                segment[h.end() : headings[i + 1].start() if i + 1 < len(headings) else len(segment)].strip(),
                {"heading": normalize(h[1]), "reference": normalize(h[1]).title()},
            )
            for i, h in enumerate(headings)
        ]
    raise ValueError("Unsupported parser")


def parse_letter(html, number):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one(".mw-parser-output")
    if root is None:
        raise ValueError("Wikisource article missing")
    for tag in root.select("sup.reference, .ws-noexport, .pagenum, .mw-editsection"):
        tag.decompose()
    paragraphs = [p.get_text("", strip=False).replace("\u200b", "").strip() for p in root.select("p")]
    text = "\n\n".join(p for p in paragraphs if p)
    # Paragraph numbers are printed as superscript numeric markers.
    matches = list(re.finditer(r"(?:^|\s)(\d+)\.\s*", text))
    if not matches or matches[0][1] != "1":
        raise ValueError("Letter paragraph numbering unavailable")
    units = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        excerpt = text[m.end() : end].strip()
        units.append(
            (
                f"{number}.{m[1]}",
                excerpt,
                {
                    "letter_number": number,
                    "section_number": int(m[1]),
                    "reference": f"Letter {number}, paragraph {m[1]}",
                },
            )
        )
    return units
