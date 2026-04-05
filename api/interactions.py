# docs: https://vercel.com/docs/functions/functions-api-reference/vercel-sdk-python
from http.server import BaseHTTPRequestHandler
import json
import os
import random
import urllib.error
import urllib.request
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

REDDIT_URL = "https://www.reddit.com/r/aww/hot.json"
USER_AGENT = "awwbot:vercel-python:v1.0.0 (by /u/justinblat)"

AWW_COMMAND = {
    "name": "awwww",
    "description": "Drop some cuteness on this channel.",
}

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


def _get_cute_url() -> str | None:
    request = urllib.request.Request(
        REDDIT_URL,
        headers={"User-Agent": USER_AGENT},
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        return None

    posts = []
    for post in data.get("data", {}).get("children", []):
        post_data = post.get("data", {})
        if post_data.get("is_gallery"):
            continue

        url = (
            (post_data.get("media") or {}).get("reddit_video", {}).get("fallback_url")
            or (post_data.get("secure_media") or {})
            .get("reddit_video", {})
            .get("fallback_url")
            or post_data.get("url")
        )

        if url:
            posts.append(url)

    if not posts:
        return None

    return random.choice(posts)




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
            cute_url = _get_cute_url() or "No content available at the moment, please try again later."
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


class handler(BaseHTTPRequestHandler):
    def _handle(self):
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
