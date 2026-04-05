# docs: https://vercel.com/docs/functions/functions-api-reference/vercel-sdk-python
import json
import os
from http.server import BaseHTTPRequestHandler
from typing import Any

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

# Discord interaction types
INTERACTION_TYPE_PING = 1
INTERACTION_TYPE_APPLICATION_COMMAND = 2

# Discord interaction response types
INTERACTION_RESPONSE_TYPE_PONG = 1
INTERACTION_RESPONSE_TYPE_CHANNEL_MESSAGE_WITH_SOURCE = 4

# Discord message flags
MESSAGE_FLAG_EPHEMERAL = 64

INVITE_COMMAND = {
    "name": "invite",
    "description": "Get an invite link to add the bot to your server",
}


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
    """Handle Discord interaction requests.

    Args:
        method: HTTP method (for example, GET or POST).
        path: Request path; only /api/interactions is handled.
        headers: Lowercased request headers.
        body_text: Raw request body as UTF-8 text.
        env: Optional environment variable mapping; defaults to os.environ.

    Returns:
        A tuple of (status_code, response_headers, response_body_text).
    """
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


class handler(BaseHTTPRequestHandler):
    def _handle(self):
        """Read the incoming request and write the mapped interaction response."""
        content_length = int(self.headers.get("content-length", "0"))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""

        normalized_headers = {k.lower(): v for k, v in self.headers.items()}
        status, response_headers, response_body = handle_interaction_request(
            method=self.command,
            path=self.path,
            headers=normalized_headers,
            body_text=body,
        )

        self.send_response(status)
        for key, value in response_headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(response_body.encode("utf-8"))

    def do_HEAD(self):
        status, response_headers, _ = handle_interaction_request(
            method="GET",
            path=self.path,
            headers={k.lower(): v for k, v in self.headers.items()},
            body_text="",
        )
        self.send_response(status)
        for key, value in response_headers.items():
            self.send_header(key, value)
        self.end_headers()

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()
