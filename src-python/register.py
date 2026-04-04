"""
Register all slash commands with the Discord API.

This script is meant to be run from the command line once, before deploying
the bot. It reads credentials from a .dev.vars file or environment variables.

Usage:
    python src-python/register.py
"""

import json
import os
import urllib.error
import urllib.request

from commands import AWW_COMMAND, INVITE_COMMAND


def load_dev_vars(path=".dev.vars"):
    """Load KEY=VALUE pairs from a Wrangler .dev.vars file."""
    vars_ = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    vars_[key.strip()] = value.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return vars_


def main():
    dev_vars = load_dev_vars()

    token = os.environ.get("DISCORD_TOKEN") or dev_vars.get("DISCORD_TOKEN")
    application_id = os.environ.get("DISCORD_APPLICATION_ID") or dev_vars.get(
        "DISCORD_APPLICATION_ID"
    )

    if not token:
        raise ValueError("The DISCORD_TOKEN environment variable is required.")
    if not application_id:
        raise ValueError(
            "The DISCORD_APPLICATION_ID environment variable is required."
        )

    url = f"https://discord.com/api/v10/applications/{application_id}/commands"
    payload = json.dumps([AWW_COMMAND, INVITE_COMMAND]).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        method="PUT",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bot {token}",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print("Registered all commands")
            print(json.dumps(data, indent=2))
    except urllib.error.HTTPError as e:
        error_text = f"Error registering commands\n{url}: {e.code} {e.reason}"
        try:
            body = e.read().decode("utf-8")
            if body:
                error_text = f"{error_text}\n\n{body}"
        except Exception:
            pass
        print(error_text)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
