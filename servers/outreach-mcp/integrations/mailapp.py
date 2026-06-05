"""Local macOS Mail.app send — the zero-OAuth fallback (KTD3). Drives Mail via
AppleScript using whatever account Mail is already signed into. No API keys, no
Cloud Console. macOS only."""
import subprocess


def _escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def send(to, subject, body):
    """Compose and send an email through the local Mail.app. Returns True on success."""
    script = f'''
    tell application "Mail"
        set newMsg to make new outgoing message with properties {{subject:"{_escape(subject)}", content:"{_escape(body)}", visible:false}}
        tell newMsg
            make new to recipient at end of to recipients with properties {{address:"{_escape(to)}"}}
            send
        end tell
    end tell
    '''
    proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Mail.app send failed: {proc.stderr.strip()}")
    return True


def available():
    """True if running on macOS with osascript present."""
    import shutil
    return shutil.which("osascript") is not None
