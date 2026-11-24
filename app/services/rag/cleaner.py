import re
import unicodedata

class TextCleaner:
    """Cleans extracted document text while preserving headings and structural context."""

    @staticmethod
    def clean(text: str) -> str:
        """
        Cleans and normalizes text:
        - Normalizes Unicode characters (NFKC)
        - Removes non-printable control characters (except newlines and tabs)
        - Normalizes Windows (\r\n) to standard (\n)
        - Strips trailing/leading spaces on lines
        - Condenses multiple excessive blank lines (>2) into two newlines
        - Preserves markdown headers, bullet points, numbered lists
        """
        if not text:
            return ""

        # Normalize unicode
        text = unicodedata.normalize("NFKC", text)

        # Normalize carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove control characters except standard whitespace
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

        # Strip line-level whitespace
        lines = [line.strip() for line in text.split("\n")]

        # Condense consecutive blank lines to at most 2
        cleaned_lines = []
        consecutive_blank = 0
        for line in lines:
            if not line:
                consecutive_blank += 1
                if consecutive_blank <= 1:
                    cleaned_lines.append("")
            else:
                consecutive_blank = 0
                cleaned_lines.append(line)

        cleaned_text = "\n".join(cleaned_lines).strip()
        return cleaned_text
