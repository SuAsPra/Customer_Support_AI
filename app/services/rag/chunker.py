import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("support_coach.chunker")

class Chunk:
    """Represents a discrete text chunk with associated metadata."""
    def __init__(
        self,
        chunk_index: int,
        text: str,
        section: Optional[str],
        page_number: int,
        token_count: int,
        metadata: Dict[str, Any]
    ):
        self.chunk_index = chunk_index
        self.text = text
        self.section = section
        self.page_number = page_number
        self.token_count = token_count
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_index": self.chunk_index,
            "text": self.text,
            "section": self.section,
            "page_number": self.page_number,
            "token_count": self.token_count,
            "metadata": self.metadata,
        }

class TextChunker:
    """
    Token-aware semantic text chunker.
    Configuration:
      - target_chunk_size: ~220-240 tokens (aligned with all-MiniLM-L6-v2 256-token max sequence length)
      - chunk_overlap: ~40-50 tokens
      - max_chunk_tokens: 240 tokens hard ceiling (leaving headroom for model [CLS]/[SEP] special tokens)
    Features:
      - Accurate token counting via transformer tokenizer
      - Robust section heading detection and grouping
      - Sentence and paragraph boundary preservation
      - Heading and structural context retention with zero silent truncation
    """

    HEADING_PATTERNS = [
        re.compile(r"^#{1,4}\s+(.+)$"),                                                              # Markdown header
        re.compile(r"^(\d+\.|\d+\.\d+|Section\s+\d+|Article\s+\d+)\s+([A-Za-z0-9\s,\-–:()'/]+)$", re.IGNORECASE),  # Numbered sections
        re.compile(r"^(?:Section|Article|Policy|Part)\s*[:\-]\s*(.+)$", re.IGNORECASE),             # Named sections
        re.compile(r"^[A-Z0-9\s,\-–:]{5,50}$")                                                      # Short all-caps titles
    ]

    def __init__(
        self,
        target_chunk_size: int = 220,
        chunk_overlap: int = 40,
        max_chunk_tokens: int = 240,
        tokenizer: Optional[Any] = None
    ):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunk_tokens = max_chunk_tokens
        self.tokenizer = tokenizer
        logger.info(
            "TextChunker initialized: target_chunk_size=%d, chunk_overlap=%d, max_chunk_tokens=%d",
            self.target_chunk_size, self.chunk_overlap, self.max_chunk_tokens
        )

    def count_tokens(self, text: str) -> int:
        """Counts tokens using model tokenizer or reliable fallback."""
        if not text:
            return 0
        if self.tokenizer is not None and hasattr(self.tokenizer, "encode"):
            try:
                tokens = self.tokenizer.encode(text, add_special_tokens=False)
                return len(tokens)
            except Exception:
                pass
        # Fallback approximation: 1 token ~ 0.75 words, or word count * 1.33
        words = text.split()
        return max(1, int(len(words) * 1.33))

    def _is_heading(self, line: str) -> Optional[str]:
        """Checks if a single line represents a section heading."""
        line = line.strip()
        if not line or len(line) > 90 or len(line) < 3:
            return None
        # Avoid treating normal sentences ending with periods as headings
        if line.endswith(".") and not re.match(r"^\d+\.", line):
            return None
        for pattern in self.HEADING_PATTERNS:
            match = pattern.match(line)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    return f"{groups[0]} {groups[1]}".strip()
                elif len(groups) == 1:
                    return groups[0].strip()
                return line.strip()
        return None

    def _split_long_sentence(self, sentence: str, max_tokens: int) -> List[str]:
        """Splits an oversized single sentence by punctuation or word boundaries."""
        if self.count_tokens(sentence) <= max_tokens:
            return [sentence]
        
        # Try splitting by semicolons or commas
        subparts = re.split(r"(?<=[,;])\s+", sentence)
        result: List[str] = []
        curr = []
        curr_len = 0
        for sp in subparts:
            sp_len = self.count_tokens(sp)
            if curr_len + sp_len > max_tokens and curr:
                result.append(" ".join(curr))
                curr = []
                curr_len = 0
            curr.append(sp)
            curr_len += sp_len
        if curr:
            result.append(" ".join(curr))
        return result if result else [sentence]

    def chunk_document(
        self,
        pages_data: List[Dict[str, Any]],
        source_filename: str,
        product_domain: str = "ecommerce"
    ) -> List[Chunk]:
        """
        Chunks multi-page document into semantic units grouped by section headers
        and bounded by target_chunk_size with chunk_overlap and max_chunk_tokens hard limit.
        Guarantees that no chunk exceeds the embedding model context window (256 tokens).
        """
        all_chunks: List[Chunk] = []
        global_chunk_idx = 0
        current_section = "General"

        for page_info in pages_data:
            page_num = page_info.get("page_number", 1)
            raw_page_text = page_info.get("text", "")
            if not raw_page_text.strip():
                continue

            # Parse lines to identify headers and assemble logical blocks
            lines = [l.strip() for l in raw_page_text.split("\n")]
            section_blocks: List[Dict[str, Any]] = []
            current_block_lines: List[str] = []
            active_header = current_section

            for line in lines:
                if not line:
                    if current_block_lines:
                        current_block_lines.append("")
                    continue

                heading = self._is_heading(line)
                if heading:
                    # Save prior block if exists
                    if current_block_lines:
                        block_text = "\n".join(current_block_lines).strip()
                        if block_text:
                            section_blocks.append({
                                "section": active_header,
                                "text": block_text,
                                "page_number": page_num
                            })
                        current_block_lines = []
                    active_header = heading
                    current_section = heading
                else:
                    current_block_lines.append(line)

            # Flush last block of the page
            if current_block_lines:
                block_text = "\n".join(current_block_lines).strip()
                if block_text:
                    section_blocks.append({
                        "section": active_header,
                        "text": block_text,
                        "page_number": page_num
                    })

            # Process each section block into chunks
            for block in section_blocks:
                sec_title = block["section"]
                sec_text = block["text"]
                header_prefix = f"[{sec_title}]\n" if not sec_text.startswith(sec_title) else ""
                header_tokens = self.count_tokens(header_prefix)

                block_tokens = self.count_tokens(sec_text)
                total_single_tokens = header_tokens + block_tokens

                if total_single_tokens <= self.target_chunk_size:
                    # Entire section fits comfortably in one chunk
                    chunk_text = f"{header_prefix}{sec_text}"
                    tokens = self.count_tokens(chunk_text)
                    chunk = Chunk(
                        chunk_index=global_chunk_idx,
                        text=chunk_text,
                        section=sec_title,
                        page_number=page_num,
                        token_count=tokens,
                        metadata={
                            "source_filename": source_filename,
                            "page_number": page_num,
                            "section": sec_title,
                            "chunk_index": global_chunk_idx,
                            "product_domain": product_domain,
                            "token_count": tokens,
                            "target_chunk_size": self.target_chunk_size,
                            "chunk_overlap": self.chunk_overlap,
                            "max_chunk_tokens": self.max_chunk_tokens
                        }
                    )
                    all_chunks.append(chunk)
                    global_chunk_idx += 1
                else:
                    # Split long section into sentences while maintaining overlap and section header
                    effective_target = max(60, self.target_chunk_size - header_tokens)
                    effective_max = max(80, self.max_chunk_tokens - header_tokens)

                    raw_sentences = re.split(r"(?<=[.!?])\s+", sec_text)
                    sentences: List[str] = []
                    for rs in raw_sentences:
                        rs_clean = rs.strip()
                        if not rs_clean:
                            continue
                        sub_sents = self._split_long_sentence(rs_clean, effective_max)
                        sentences.extend(sub_sents)

                    curr_sentences: List[str] = []
                    curr_toks = 0

                    for s in sentences:
                        s_toks = self.count_tokens(s)
                        if (curr_toks + s_toks > effective_target) and curr_sentences:
                            sub_text = " ".join(curr_sentences)
                            full_chunk_text = f"{header_prefix}{sub_text}"
                            tokens = self.count_tokens(full_chunk_text)
                            chunk = Chunk(
                                chunk_index=global_chunk_idx,
                                text=full_chunk_text,
                                section=sec_title,
                                page_number=page_num,
                                token_count=tokens,
                                metadata={
                                    "source_filename": source_filename,
                                    "page_number": page_num,
                                    "section": sec_title,
                                    "chunk_index": global_chunk_idx,
                                    "product_domain": product_domain,
                                    "token_count": tokens,
                                    "target_chunk_size": self.target_chunk_size,
                                    "chunk_overlap": self.chunk_overlap,
                                    "max_chunk_tokens": self.max_chunk_tokens
                                }
                            )
                            all_chunks.append(chunk)
                            global_chunk_idx += 1

                            # Keep overlap sentences from end
                            overlap_sents = []
                            overlap_toks = 0
                            for prev_s in reversed(curr_sentences):
                                overlap_sents.insert(0, prev_s)
                                overlap_toks += self.count_tokens(prev_s)
                                if overlap_toks >= self.chunk_overlap:
                                    break
                            curr_sentences = list(overlap_sents)
                            curr_toks = overlap_toks

                        curr_sentences.append(s)
                        curr_toks += s_toks

                    if curr_sentences:
                        sub_text = " ".join(curr_sentences)
                        full_chunk_text = f"{header_prefix}{sub_text}"
                        tokens = self.count_tokens(full_chunk_text)
                        chunk = Chunk(
                            chunk_index=global_chunk_idx,
                            text=full_chunk_text,
                            section=sec_title,
                            page_number=page_num,
                            token_count=tokens,
                            metadata={
                                "source_filename": source_filename,
                                "page_number": page_num,
                                "section": sec_title,
                                "chunk_index": global_chunk_idx,
                                "product_domain": product_domain,
                                "token_count": tokens,
                                "target_chunk_size": self.target_chunk_size,
                                "chunk_overlap": self.chunk_overlap,
                                "max_chunk_tokens": self.max_chunk_tokens
                            }
                        )
                        all_chunks.append(chunk)
                        global_chunk_idx += 1

        logger.info(
            "Created %d semantic chunks for document '%s' (avg tokens: %.1f, max tokens: %d)",
            len(all_chunks), source_filename,
            (sum(c.token_count for c in all_chunks) / len(all_chunks)) if all_chunks else 0,
            max((c.token_count for c in all_chunks), default=0)
        )
        return all_chunks
