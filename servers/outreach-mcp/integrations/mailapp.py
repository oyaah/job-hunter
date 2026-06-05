"""Local macOS Mail.app send — the zero-OAuth fallback (KTD3). Drives Mail via
AppleScript using whatever account Mail is already signed into. No API keys, no
Cloud Console. macOS only."""
import subprocess

# Subject/body/to are passed as osascript argv (`on run argv`), NOT interpolated
# into the script text. This makes injection impossible (no string-literal breakout)
# and handles newlines/quotes/backslashes in the body correctly — string
# interpolation did neither.
_SCRIPT = '''
on run argv
    set theTo to item 1 of argv
    set theSubject to item 2 of argv
    set theBody to item 3 of argv
    tell application "Mail"
        set newMsg to make new outgoing message with properties {subject:theSubject, content:theBody, visible:false}
        tell newMsg
            make new to recipient at end of to recipients with properties {address:theTo}
            send
        end tell
    end tell
end run
'''


def send(to, subject, body):
    """Compose and send an email through the local Mail.app. Returns True on success.
    Fields are passed as argv, so any content (newlines, quotes) is safe and literal."""
    proc = subprocess.run(["osascript", "-e", _SCRIPT, to, subject, body],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Mail.app send failed: {proc.stderr.strip()}")
    return True


def available():
    """True if running on macOS with osascript present."""
    import shutil
    return shutil.which("osascript") is not None
