"""Self-evolving reflection — threshold-triggered distillation."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servers", "outreach-mcp"))

import store  # noqa: E402
import learnings  # noqa: E402
import distill  # noqa: E402


def fresh():
    return store.connect(":memory:")


def test_not_due_below_threshold():
    conn = fresh()
    learnings.record(conn, "voice", "a", weight=3.0)
    assert distill.is_due(conn) is False


def test_due_at_threshold():
    conn = fresh()
    for i in range(10):
        learnings.record(conn, "voice", f"insight {i}", weight=1.0)
    assert distill.pending_weight(conn) >= distill.THRESHOLD
    assert distill.is_due(conn) is True


def test_material_ordered_by_weight():
    conn = fresh()
    learnings.record(conn, "voice", "weak", weight=1.0)
    learnings.record(conn, "voice", "strong", weight=9.0)
    mat = distill.material(conn, "voice")
    assert mat[0]["insight"] == "strong"


def test_apply_caps_bytes_and_marks_distilled():
    conn = fresh()
    for i in range(12):
        learnings.record(conn, "voice", f"insight {i}", weight=1.0)
    big = "\n".join(f"principle line {i} " + "x" * 80 for i in range(60))  # > 2000 bytes
    res = distill.apply(conn, "voice", big)
    assert res["bytes"] <= distill.PROFILE_CAP
    # pending weight for voice is now zero (all marked distilled)
    assert distill.pending_weight(conn, "voice") == 0
    # raw learnings still exist (audit trail)
    assert len(learnings.get(conn, "voice")) == 12


def test_apply_only_marks_its_category():
    conn = fresh()
    learnings.record(conn, "voice", "v", weight=5.0)
    learnings.record(conn, "targeting", "t", weight=5.0)
    distill.apply(conn, "voice", "principle")
    assert distill.pending_weight(conn, "voice") == 0
    assert distill.pending_weight(conn, "targeting") == 5.0  # untouched


def test_profile_roundtrip():
    conn = fresh()
    distill.apply(conn, "voice", "lead with the war story")
    assert "war story" in distill.get_profile(conn, "voice")
    assert distill.get_profile(conn, "targeting") == ""
