"""U3 — voice anti-AI lint."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servers", "outreach-mcp"))

import voice  # noqa: E402


def test_clean_message_passes():
    good = ("Hey Jane, I'm Sam, a backend dev who builds payment systems. "
            "Saw your work on the fraud pipeline. Would you be open to a quick chat? Thanks!")
    assert voice.lint(good) == []
    assert voice.is_clean(good)


def test_em_dash_flagged():
    issues = voice.lint("I build systems — and I ship them.")
    assert any(i["type"] == "em_dash" for i in issues)


def test_en_dash_flagged():
    assert any(i["type"] == "em_dash" for i in voice.lint("ranges 1–10 here"))


def test_banned_opener_flagged():
    issues = voice.lint("I am writing to express my keen interest in the role.")
    assert any(i["type"] == "ai_cadence" for i in issues)


def test_banned_words_flagged():
    issues = voice.lint("I leverage cutting-edge tools and utilize robust pipelines.")
    types = [i["match"] for i in issues]
    assert "leverage" in types and "utilize" in types and "robust" in types


def test_case_insensitive():
    assert any(i["type"] == "ai_cadence"
               for i in voice.lint("I HOPE THIS EMAIL FINDS YOU WELL today"))


def test_word_boundary_no_false_positive():
    # 'utilize' substring should not trip on unrelated words
    assert voice.is_clean("The util function returns fast. Thanks!")
