# docs: https://vercel.com/docs/functions/functions-api-reference/vercel-sdk-python
from http.server import BaseHTTPRequestHandler
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PYTHON = PROJECT_ROOT / "src-python"
if str(SRC_PYTHON) not in sys.path:
    sys.path.insert(0, str(SRC_PYTHON))

from server import handle_interaction_request


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
