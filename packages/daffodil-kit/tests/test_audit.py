"""Audit log tests."""

from daffodil_kit.audit import log_event, read_audit_tail, read_kit_log_tail


def test_log_event_and_tail(tmp_path, monkeypatch):
    audit_file = tmp_path / "copycat_audit.jsonl"
    kit_log = tmp_path / "kit.log"
    monkeypatch.setattr("daffodil_kit.audit.AUDIT_DIR", tmp_path)
    monkeypatch.setattr("daffodil_kit.audit.AUDIT_FILE", audit_file)
    monkeypatch.setattr("daffodil_kit.audit.KIT_LOG_FILE", kit_log)

    e1 = log_event("test.event", detail={"n": 1})
    log_event("test.event", detail={"n": 2}, level="warn")

    assert e1["event"] == "test.event"
    tail = read_audit_tail(10)
    assert len(tail) == 2
    assert tail[-1]["detail"]["n"] == 2

    lines = read_kit_log_tail(5)
    assert len(lines) >= 2
