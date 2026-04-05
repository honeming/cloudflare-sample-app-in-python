"""Discord interaction handling for Vercel Python Functions."""

import json
import os
from typing import Any

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from commands import AWW_COMMAND, INVITE_COMMAND
from reddit import get_cute_url

# Discord interaction types
INTERACTION_TYPE_PING = 1
INTERACTION_TYPE_APPLICATION_COMMAND = 2

# Discord interaction response types
INTERACTION_RESPONSE_TYPE_PONG = 1
INTERACTION_RESPONSE_TYPE_CHANNEL_MESSAGE_WITH_SOURCE = 4

# Discord message flags
MESSAGE_FLAG_EPHEMERAL = 64


def _json_response(body_dict: dict[str, Any], status: int = 200) -> tuple[int, dict[str, str], str]:
    return (
        status,
        {"Content-Type": "application/json;charset=UTF-8"},
        json.dumps(body_dict),
    )


def _verify_discord_request(signature: str | None, timestamp: str | None, body: str, public_key: str) -> bool:
    if not signature or not timestamp or not public_key:
        return False

    try:
        verify_key = VerifyKey(bytes.fromhex(public_key))
        verify_key.verify(f"{timestamp}{body}".encode("utf-8"), bytes.fromhex(signature))
        return True
    except (ValueError, BadSignatureError):
        return False


def handle_interaction_request(
    method: str,
    path: str,
    headers: dict[str, str],
    body_text: str,
    env: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], str]:
    env_vars = env or os.environ

    if method == "GET" and path == "/api/interactions":
        return 200, {"Content-Type": "text/plain;charset=UTF-8"}, "OK"

    if method != "POST" or path != "/api/interactions":
        return 404, {"Content-Type": "text/plain;charset=UTF-8"}, "Not Found."

    signature = headers.get("x-signature-ed25519")
    timestamp = headers.get("x-signature-timestamp")

    if not _verify_discord_request(
        signature,
        timestamp,
        body_text,
        env_vars.get("DISCORD_PUBLIC_KEY", ""),
    ):
        return 401, {"Content-Type": "text/plain;charset=UTF-8"}, "Bad request signature."

    try:
        interaction = json.loads(body_text)
    except json.JSONDecodeError:
        return _json_response({"error": "Invalid JSON body"}, status=400)

    if interaction.get("type") == INTERACTION_TYPE_PING:
        return _json_response({"type": INTERACTION_RESPONSE_TYPE_PONG})

    if interaction.get("type") == INTERACTION_TYPE_APPLICATION_COMMAND:
        command_name = ((interaction.get("data") or {}).get("name") or "").lower()

        if command_name == AWW_COMMAND["name"].lower():
            cute_url = get_cute_url() or "目前沒有可用內容，請稍後再試。"
            return _json_response(
                {
                    "type": INTERACTION_RESPONSE_TYPE_CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {"content": cute_url},
                }
            )

        if command_name == INVITE_COMMAND["name"].lower():
            application_id = env_vars.get("DISCORD_APPLICATION_ID", "")
            invite_url = (
                "https://discord.com/oauth2/authorize"
                f"?client_id={application_id}&scope=applications.commands"
            )
            return _json_response(
                {
                    "type": INTERACTION_RESPONSE_TYPE_CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": invite_url,
                        "flags": MESSAGE_FLAG_EPHEMERAL,
                    },
                }
            )

    return _json_response({"error": "Unknown Type"}, status=400)
