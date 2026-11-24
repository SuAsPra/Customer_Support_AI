import io
import logging
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader
from pypdf.errors import PdfReadError

logger = logging.getLogger("support_coach.extractor")

class DocumentExtractionError(Exception):
    """Base exception for document extraction failures."""
    pass

class CorruptedDocumentError(DocumentExtractionError):
    """Raised when the document is unreadable or corrupted."""
    pass

class EmptyDocumentError(DocumentExtractionError):
    """Raised when the document contains no extractable text."""
    pass

class DocumentExtractor:
    """Extracts text from PDF and text-based documents while preserving page numbers."""

    @staticmethod
    def extract_from_bytes(
        file_bytes: bytes, filename: str, doc_type: str = "pdf"
    ) -> List[Dict[str, Any]]:
        """
        Extracts text from raw bytes.
        Returns a list of page dicts: [{"page_number": int, "text": str}]
        """
        if not file_bytes or len(file_bytes.strip()) == 0:
            raise EmptyDocumentError(f"File '{filename}' is completely empty (0 bytes).")

        doc_type_lower = doc_type.lower()
        if filename.endswith(".pdf") or doc_type_lower == "pdf":
            return DocumentExtractor._extract_pdf(file_bytes, filename)
        elif filename.endswith((".txt", ".md", ".json")) or doc_type_lower in ["txt", "markdown", "text"]:
            return DocumentExtractor._extract_text(file_bytes, filename)
        else:
            # Fallback attempt to decode as text
            try:
                return DocumentExtractor._extract_text(file_bytes, filename)
            except Exception as e:
                raise DocumentExtractionError(
                    f"Unsupported or unreadable document format for '{filename}': {str(e)}"
                )

    @staticmethod
    def _extract_pdf(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        """Extracts text from PDF bytes page by page."""
        try:
            stream = io.BytesIO(file_bytes)
            reader = PdfReader(stream)
        except (PdfReadError, Exception) as e:
            logger.error("Failed to parse PDF '%s': %s", filename, str(e))
            raise CorruptedDocumentError(f"Corrupted or invalid PDF file '{filename}': {str(e)}")

        if reader.is_encrypted:
            try:
                # Attempt empty password decrypt
                reader.decrypt("")
            except Exception:
                raise CorruptedDocumentError(f"PDF file '{filename}' is encrypted and password-protected.")

        pages_data: List[Dict[str, Any]] = []
        total_text_length = 0

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            try:
                page_text = page.extract_text() or ""
            except Exception as e:
                logger.warning("Error extracting text on page %d of '%s': %s", page_num, filename, str(e))
                page_text = ""

            page_text_clean = page_text.strip()
            total_text_length += len(page_text_clean)
            if page_text_clean:
                pages_data.append({
                    "page_number": page_num,
                    "text": page_text
                })

        if total_text_length == 0:
            raise EmptyDocumentError(
                f"PDF file '{filename}' contains {len(reader.pages)} pages, but no extractable text could be found."
            )

        logger.info("Successfully extracted %d non-empty pages from PDF '%s'", len(pages_data), filename)
        return pages_data

    @staticmethod
    def _extract_text(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        """Extracts plain text / markdown files."""
        text = None
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                text = file_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise CorruptedDocumentError(f"Could not decode text file '{filename}' with supported encodings.")

        text_clean = text.strip()
        if not text_clean:
            raise EmptyDocumentError(f"Text file '{filename}' contains no content.")

        return [{
            "page_number": 1,
            "text": text
        }]
