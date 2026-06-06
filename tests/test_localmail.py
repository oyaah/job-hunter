"""Cross-platform local-mail backend selection + send semantics.

We can't run Mail.app / Outlook / Thunderbird in CI, so we mock platform.system,
shutil.which, and subprocess.run and assert (a) the right backend is picked per OS,
(b) sent-vs-composed is reported honestly, and (c) user-controlled fields are passed
as argv/env, never interpolated into a shell string."""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servers", "outreach-mcp"))

from integrations import localmail  # noqa: E402


class _Proc:
    def __init__(self, returncode=0, stderr=""):
        self.returncode = returncode
        self.stderr = stderr


def _patch(monkeypatch, system, which=lambda c: "/usr/bin/" + c):
    monkeypatch.setattr(localmail.platform, "system", lambda: system)
    monkeypatch.setattr(localmail.shutil, "which", which)


def test_macos_sends(monkeypatch):
    _patch(monkeypatch, "Darwin")
    calls = {}

    def fake_run(args, **kw):
        calls["args"] = args
        return _Proc(0)

    monkeypatch.setattr(localmail.subprocess, "run", fake_run)
    res = localmail.send("a@b.com", "Sub, with comma", "Body\nwith 'quotes'")
    assert res == {"delivery": "sent", "via": "macos-mail"}
    # to/subject/body ride as osascript argv (positions -3,-2,-1), not interpolated.
    assert calls["args"][0] == "osascript"
    assert calls["args"][-3:] == ["a@b.com", "Sub, with comma", "Body\nwith 'quotes'"]


def test_windows_outlook_sends(monkeypatch):
    _patch(monkeypatch, "Windows")
    seen = {}

    def fake_run(args, **kw):
        seen["env"] = kw.get("env", {})
        return _Proc(0)  # Outlook COM succeeds

    monkeypatch.setattr(localmail.subprocess, "run", fake_run)
    res = localmail.send("a@b.com", "S", "B")
    assert res == {"delivery": "sent", "via": "windows-outlook"}
    # Fields passed via env, never string-built into the PowerShell command.
    assert seen["env"]["JH_TO"] == "a@b.com" and seen["env"]["JH_BODY"] == "B"


def test_windows_falls_back_to_mailto_compose(monkeypatch):
    _patch(monkeypatch, "Windows")
    runs = []

    def fake_run(args, **kw):
        runs.append(args)
        return _Proc(1) if "powershell" in args[0] else _Proc(0)  # Outlook missing

    monkeypatch.setattr(localmail.subprocess, "run", fake_run)
    res = localmail.send("a@b.com", "S", "B")
    assert res["delivery"] == "composed" and res["via"] == "windows-mailto"
    assert runs[-1][:3] == ["cmd", "/c", "start"]
    assert runs[-1][-1].startswith("mailto:a%40b.com")


def test_linux_xdg_composes(monkeypatch):
    _patch(monkeypatch, "Linux", which=lambda c: "/usr/bin/xdg-email" if c == "xdg-email" else None)
    runs = []
    monkeypatch.setattr(localmail.subprocess, "run", lambda a, **k: runs.append(a) or _Proc(0))
    res = localmail.send("a@b.com", "S", "B")
    assert res == {"delivery": "composed", "via": "linux-xdg"}
    assert runs[0] == ["xdg-email", "--subject", "S", "--body", "B", "a@b.com"]


def test_linux_no_client_raises(monkeypatch):
    _patch(monkeypatch, "Linux", which=lambda c: None)
    assert localmail.available() is False
    try:
        localmail.send("a@b.com", "S", "B")
        assert False, "expected RuntimeError"
    except RuntimeError as e:
        assert "no local mail client" in str(e)


def test_describe_is_honest_about_compose(monkeypatch):
    _patch(monkeypatch, "Linux", which=lambda c: "/usr/bin/xdg-email" if c == "xdg-email" else None)
    assert "composes" in localmail.describe()
