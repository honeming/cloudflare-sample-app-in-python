"""
Print a curl command to register slash commands with the Discord API.

This script is meant to be run from the command line once, before deploying
or after command schema changes. It reads credentials from a .dev.vars file
or environment variables.

Usage:
    python src-python/register.py
"""

import json
import os
import shlex

from commands import AWW_COMMAND, INVITE_COMMAND


def load_dev_vars(path=".dev.vars"):
    """Load KEY=VALUE pairs from a .dev.vars file."""
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

    application_id = os.environ.get("DISCORD_APPLICATION_ID") or dev_vars.get(
        "DISCORD_APPLICATION_ID"
    )

    if not application_id:
        raise ValueError("The DISCORD_APPLICATION_ID environment variable is required.")

    url = f"https://discord.com/api/v10/applications/{application_id}/commands"
    payload = json.dumps([AWW_COMMAND, INVITE_COMMAND], separators=(",", ":"))

    curl_command = " ".join(
        [
            "curl",
            "-X",
            "PUT",
            shlex.quote(url),
            "-H",
            shlex.quote("Content-Type: application/json"),
            "-H",
            shlex.quote("Authorization: Bot $DISCORD_TOKEN"),
            "--data-raw",
            shlex.quote(payload),
        ]
    )

    print("請先確認已設定 DISCORD_TOKEN，然後執行以下指令註冊命令：")
    print(curl_command)


if __name__ == "__main__":
    main()
