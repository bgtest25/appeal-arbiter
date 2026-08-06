"""Parses Swypi's real community guidelines into retrieval chunks.

Chunk boundaries follow the document's own structure, at bullet-item
granularity: each <li> becomes its own chunk under its nearest heading,
and each <p>/<div> becomes its own chunk. Bullet-level granularity matters
here specifically — grouping a whole category's bullets into one blob (e.g.
all 7 "Monetization fraud & abuse" items) dilutes distinctive phrases like
"Sealed Posts" into an averaged embedding that a short, informal appeal
query won't match well; one vector per violation retrieves far more
precisely.
"""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup, Tag

SOURCE_PATH = Path(__file__).parent / "source_docs" / "community-guidelines.html"


@dataclass
class GuidelineChunk:
    id: str
    section: str
    title: str
    text: str


def _slugify(title: str) -> str:
    return title.lower().replace("&", "and").replace(" ", "-").replace("'", "")


def _text(el: Tag) -> str:
    # get_text(strip=True) with the default separator="" strips each text
    # fragment individually before joining, which eats the whitespace either
    # side of inline tags like <strong>/<em> (e.g. "onSealed Postswith").
    # separator=" " avoids that; the .split()/" ".join collapses the
    # resulting double spaces back down to single ones.
    return " ".join(el.get_text(separator=" ", strip=True).split())


def parse_guidelines(source_path: Path = SOURCE_PATH) -> list[GuidelineChunk]:
    html = source_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main", class_="legal-content")

    chunks: list[GuidelineChunk] = []
    counts: dict[str, int] = defaultdict(int)

    def emit(section: str, title: str, text: str) -> None:
        text = text.strip()
        if not text:
            return
        slug = _slugify(title)
        counts[slug] += 1
        chunk_id = slug if counts[slug] == 1 else f"{slug}-{counts[slug]}"
        chunks.append(GuidelineChunk(id=chunk_id, section=section, title=title, text=text))

    current_section = "Overview"
    current_title = "Overview"
    for el in main.children:
        if not isinstance(el, Tag):
            continue
        if el.name == "h1":
            continue
        if el.name == "h2":
            current_section = el.get_text(strip=True)
            current_title = current_section
        elif el.name == "h3":
            current_title = el.get_text(strip=True)
        elif el.name in ("p", "div"):
            emit(current_section, current_title, _text(el))
        elif el.name == "ul":
            for li in el.find_all("li"):
                emit(current_section, current_title, _text(li))

    return chunks


if __name__ == "__main__":
    for c in parse_guidelines():
        print(f"[{c.section}] {c.title} :: {c.text[:80]}")
