"""
The core server that runs on a Cloudflare Worker.
Reference: https://developers.cloudflare.com/workers/languages/python/
"""

import json
from urllib.parse import urlparse

from js import Object, console, crypto
from pyodide.ffi import to_js
from workers import Response, WorkerEntrypoint

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


def json_response(body_dict, status=200):
    """Return a JSON Response with the correct content-type header."""
    return Response(
        json.dumps(body_dict),
        headers=to_js(
            {"content-type": "application/json;charset=UTF-8"},
            dict_converter=Object.fromEntries,
        ),
        status=status,
    )


async def verify_discord_request(request, env):
    """
    Verify the incoming Discord request using Ed25519 signature verification
    via the Web Crypto API (SubtleCrypto).

    Returns (is_valid: bool, interaction: dict | None).
    """
    signature = request.headers.get("x-signature-ed25519")
    timestamp = request.headers.get("x-signature-timestamp")

    if not signature or not timestamp:
        return False, None

    body = await request.text()

    try:
        # Import the Ed25519 public key from raw bytes
        public_key = await crypto.subtle.importKey(
            "raw",
            to_js(bytes.fromhex(env.DISCORD_PUBLIC_KEY)),
            to_js({"name": "Ed25519"}, dict_converter=Object.fromEntries),
            False,
            to_js(["verify"]),
        )

        # The signed message is timestamp + body (both as UTF-8 bytes)
        message_bytes = (timestamp + body).encode("utf-8")

        is_valid = await crypto.subtle.verify(
            "Ed25519",
            public_key,
            to_js(bytes.fromhex(signature)),
            to_js(message_bytes),
        )

        if not is_valid:
            return False, None

        return True, json.loads(body)
    except Exception as e:
        console.error(f"Error verifying Discord request: {e}")
        return False, None


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        path = urlparse(request.url).path
        method = request.method

        # GET / — simple health-check page
        if method == "GET" and path == "/":
            return Response(f"👋 {self.env.DISCORD_APPLICATION_ID}")

        # POST / — all Discord interactions arrive here
        if method == "POST" and path == "/":
            is_valid, interaction = await verify_discord_request(request, self.env)
            if not is_valid or interaction is None:
                return Response("Bad request signature.", status=401)

            # PING: required during initial webhook handshake
            if interaction["type"] == INTERACTION_TYPE_PING:
                return json_response({"type": INTERACTION_RESPONSE_TYPE_PONG})

            # APPLICATION_COMMAND: slash commands sent by users
            if interaction["type"] == INTERACTION_TYPE_APPLICATION_COMMAND:
                command_name = interaction["data"]["name"].lower()

                if command_name == AWW_COMMAND["name"].lower():
                    cute_url = await get_cute_url()
                    return json_response(
                        {
                            "type": INTERACTION_RESPONSE_TYPE_CHANNEL_MESSAGE_WITH_SOURCE,
                            "data": {"content": cute_url},
                        }
                    )

                if command_name == INVITE_COMMAND["name"].lower():
                    application_id = self.env.DISCORD_APPLICATION_ID
                    invite_url = (
                        f"https://discord.com/oauth2/authorize"
                        f"?client_id={application_id}&scope=applications.commands"
                    )
                    return json_response(
                        {
                            "type": INTERACTION_RESPONSE_TYPE_CHANNEL_MESSAGE_WITH_SOURCE,
                            "data": {
                                "content": invite_url,
                                "flags": MESSAGE_FLAG_EPHEMERAL,
                            },
                        }
                    )

                return json_response({"error": "Unknown Type"}, status=400)

            console.error("Unknown Type")
            return json_response({"error": "Unknown Type"}, status=400)

        # All other routes
        return Response("Not Found.", status=404)
