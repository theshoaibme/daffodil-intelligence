"""Tests for general and routine PDF readers."""

import asyncio

from app.automation.routine_pdf_reader import read_routine_pdf_fast
from app.automation.routine_resolver import save_routine_upload
from app.lib.pdf_reader import read_pdf_fast
from app.tools.file.pdf_reader import ReadPdfTool


def test_read_pdf_text_file(tmp_path):
    doc = tmp_path / "notes.txt"
    doc.write_text("Line one\nLine two about CSE321\n", encoding="utf-8")

    first = read_pdf_fast(doc)
    second = read_pdf_fast(doc)

    assert first["text"] == "Line one\nLine two about CSE321"
    assert first["source"] == "text"
    assert second["cached"] is True


def test_read_pdf_query_filter(tmp_path):
    doc = tmp_path / "doc.txt"
    doc.write_text("alpha\nbeta gamma\nalpha beta\n", encoding="utf-8")

    result = read_pdf_fast(doc, query="gamma")
    assert "gamma" in result["text"]
    assert result["filtered"] is True


def test_read_pdf_tool(tmp_path):
    doc = tmp_path / "syllabus.txt"
    doc.write_text("Course syllabus content", encoding="utf-8")

    result = asyncio.run(ReadPdfTool().execute(path=str(doc)))
    assert result.success
    assert "syllabus" in result.data["text"]


def test_read_routine_pdf_fast(tmp_path, monkeypatch):
    import app.automation.routine_resolver as resolver

    monkeypatch.setattr(resolver, "ROUTINE_DATA_ROOT", tmp_path)
    save_routine_upload(
        department="TEST",
        section="99_Z",
        filename="99_Z.txt",
        content=b"Monday 10:00 CSE101 Room 1\n",
    )

    result = read_routine_pdf_fast("TEST", "99_Z")
    assert result.get("text")
    assert "Monday" in result["text"]
