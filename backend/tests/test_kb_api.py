import asyncio
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from app.api import kb


def test_upload_reports_indexing_failure_as_http_error(monkeypatch):
    def save_upload(content, filename):
        assert content == b"# FAQ"
        return filename

    def create_document(db, filename, file_path, file_type):
        assert db is None
        assert filename == file_path == "faq.md"
        assert file_type == "md"
        return SimpleNamespace(id="doc-id")

    def index_document(db, doc):
        assert db is None
        assert doc.id == "doc-id"
        return SimpleNamespace(status="failed", error="embedding failed")

    monkeypatch.setattr(kb.kb_service, "save_upload", save_upload)
    monkeypatch.setattr(
        kb.kb_service,
        "create_document",
        create_document,
    )
    monkeypatch.setattr(kb.kb_service, "index_document", index_document)
    upload = UploadFile(filename="faq.md", file=BytesIO(b"# FAQ"))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(kb.upload_document(file=upload, db=None))

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "embedding failed"
