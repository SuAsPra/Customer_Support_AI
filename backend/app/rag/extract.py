from pathlib import Path
from pypdf import PdfReader


def extract_text(file_path: str | Path, file_type: str | None = None) -> str:
    path = Path(file_path)
    suffix = (file_type or path.suffix.lstrip(".")).lower()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.stat().st_size == 0:
        return ""

    if suffix == "pdf":
        try:
            reader = PdfReader(str(path))
            parts = []
            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text() or ""
                except Exception:
                    text = ""
                if text.strip():
                    parts.append(f"[Page {i+1}]\n{text}")
            return "\n\n".join(parts).strip()
        except Exception as e:
            raise ValueError(f"Failed to read PDF: {e}")
    elif suffix in {"txt", "md", "markdown"}:
        try:
            return path.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception as e:
            raise ValueError(f"Failed to read text file: {e}")
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
