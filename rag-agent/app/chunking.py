"""Split documents into overlapping word-based chunks."""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    source: str
    index: int
    text: str


def chunk_text(source: str, text: str, size: int = 80, overlap: int = 20) -> list[Chunk]:
    """Return overlapping chunks of ~`size` words so answers aren't cut mid-idea."""
    if size <= overlap:
        raise ValueError("size must be greater than overlap")
    text = re.sub(r"^#+\s*(.+?)\s*$", r"\1.", text, flags=re.M)  # "# Title" -> "Title."
    words = text.split()
    if not words:
        return []
    step = size - overlap
    chunks = []
    for i, start in enumerate(range(0, len(words), step)):
        piece = words[start:start + size]
        chunks.append(Chunk(source=source, index=i, text=" ".join(piece)))
        if start + size >= len(words):
            break
    return chunks
