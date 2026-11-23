import re
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    index: int
    metadata: dict


def _approx_tokens_to_chars(tokens: int) -> int:
    # rough approximation: 1 token ~ 4 chars
    return max(200, tokens * 4)


def chunk_text(
    text: str,
    chunk_size_tokens: int = 450,
    overlap_tokens: int = 60,
    source: str | None = None,
) -> list[Chunk]:
    if not text or not text.strip():
        return []

    if chunk_size_tokens <= 0:
        raise ValueError("chunk_size_tokens must be greater than zero")
    if overlap_tokens < 0:
        raise ValueError("overlap_tokens cannot be negative")
    if overlap_tokens >= chunk_size_tokens:
        raise ValueError("overlap_tokens must be smaller than chunk_size_tokens")

    chunk_size = _approx_tokens_to_chars(chunk_size_tokens)
    overlap = overlap_tokens * 4
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than the chunk size")

    # Normalize and split by paragraphs/headings while keeping separators context
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p and p.strip()]

    chunks: list[Chunk] = []
    current = ""
    current_heading = None

    def flush(buf: str, heading: str | None, idx: int):
        buf = buf.strip()
        if not buf:
            return None
        meta = {"source": source}
        if heading:
            meta["section"] = heading[:120]
        return Chunk(text=buf, index=idx, metadata=meta)

    for para in paragraphs:
        # detect heading lines (# Heading or ALL CAPS short line or Title:)
        heading_match = re.match(r"^(#{1,6}\s+.+|[A-Z][A-Za-z0-9 \-/]{2,80}:?)$", para.strip())
        if heading_match and len(para.strip()) < 120:
            if current:
                ch = flush(current, current_heading, len(chunks))
                if ch:
                    chunks.append(ch)
                current = ""
            current_heading = para.strip().lstrip("#").strip()

        candidate = (current + "\n\n" + para).strip() if current else para
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                ch = flush(current, current_heading, len(chunks))
                if ch:
                    chunks.append(ch)
                # start new with overlap from end of current
                tail = current[-overlap:] if overlap > 0 else ""
                current = (tail + "\n\n" + para).strip() if tail else para
            # if single para too large, hard split
            while len(current) > chunk_size:
                cut = current[:chunk_size]
                # try to cut at sentence/space
                split_at = max(cut.rfind(". "), cut.rfind("\n"), cut.rfind(" "))
                if split_at < chunk_size * 0.5:
                    split_at = chunk_size
                part = current[:split_at].strip()
                ch = flush(part, current_heading, len(chunks))
                if ch:
                    chunks.append(ch)
                tail = part[-overlap:] if overlap > 0 else ""
                current = (tail + " " + current[split_at:]).strip()

    if current.strip():
        ch = flush(current, current_heading, len(chunks))
        if ch:
            chunks.append(ch)

    # reindex
    for i, c in enumerate(chunks):
        c.index = i
    return chunks
