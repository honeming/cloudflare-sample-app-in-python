"""
Print a curl command to register slash commands with the Discord API.

Usage:
    python register.py
"""

import json
import os
import shlex

AWW_COMMAND = {
    "name": "awwww",
    "description": "Drop some cuteness on this channel.",
}

INVITE_COMMAND = {
    "name": "invite",
    "description": "Get an invite link to add the bot to your server",
}


def load_dev_vars(path: str = ".dev.vars") -> dict[str, str]:
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


def main() -> None:
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

    print("Set DISCORD_TOKEN first, then run this command to register commands:")
    print(curl_command)


if __name__ == "__main__":
    main()
