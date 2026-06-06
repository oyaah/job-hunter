#!/usr/bin/env python3
"""Live smoke-test for the bundled LinkedIn MCP — the exact server the plugin drives.

This talks to `uvx linkedin-scraper-mcp` over stdio (same as Claude Code does) so you
can prove your LinkedIn session works and exercise the real connect/DM tools before
trusting them in a hunt. It is a TEST/diagnostic tool, not part of the plugin runtime.

First, authenticate once (opens a browser, you log in; session saved to
~/.linkedin-mcp/profile/):

    uvx linkedin-scraper-mcp@latest --login

Then:

    python3 scripts/li_smoketest.py --check                 # auth ok? lists tools + your profile
    python3 scripts/li_smoketest.py --profile williamhgates  # read a target (no action taken)
    python3 scripts/li_smoketest.py --connect <username> --note "hey, loved your X work"
    python3 scripts/li_smoketest.py --message <username> --text "thanks for connecting!"

<username> is the slug in linkedin.com/in/<username>. --connect and --message take REAL
actions on REAL people — only run them against a target you intend to contact.
"""
import argparse
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PIN = "linkedin-scraper-mcp==4.13.2"  # matches .mcp.json


def _text(result):
    """Flatten an MCP tool result into readable text."""
    out = []
    for c in result.content:
        out.append(getattr(c, "text", None) or json.dumps(getattr(c, "data", str(c))))
    return "\n".join(out)


async def run(args):
    params = StdioServerParameters(command="uvx", args=[PIN],
                                   env={"UV_HTTP_TIMEOUT": "300"})
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()

            if args.check:
                tools = await s.list_tools()
                print(f"✓ MCP up — {len(tools.tools)} tools")
                print("  auth check (get_my_profile)…")
                res = await s.call_tool("get_my_profile", {"sections": ["basics"]})
                print(_text(res)[:800])
                return

            if args.profile:
                res = await s.call_tool("get_person_profile",
                                        {"linkedin_username": args.profile,
                                         "sections": ["basics", "experience"]})
                print(_text(res)[:1200])
                return

            if args.connect:
                payload = {"linkedin_username": args.connect}
                if args.note:
                    payload["note"] = args.note
                res = await s.call_tool("connect_with_person", payload)
                print("connect_with_person →")
                print(_text(res))
                return

            if args.message:
                res = await s.call_tool("send_message",
                                        {"linkedin_username": args.message,
                                         "message": args.text,
                                         "confirm_send": True})
                print("send_message →")
                print(_text(res))
                return


def main():
    p = argparse.ArgumentParser(description="Live LinkedIn MCP smoke-test")
    p.add_argument("--check", action="store_true", help="verify auth + list tools")
    p.add_argument("--profile", metavar="USERNAME", help="read a person (no action)")
    p.add_argument("--connect", metavar="USERNAME", help="send a connection request")
    p.add_argument("--note", help="note to include with --connect")
    p.add_argument("--message", metavar="USERNAME", help="send a DM (must be 1st-degree)")
    p.add_argument("--text", help="message body for --message")
    args = p.parse_args()

    if args.message and not args.text:
        p.error("--message requires --text")
    if not any([args.check, args.profile, args.connect, args.message]):
        p.error("pick one: --check | --profile | --connect | --message")

    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
