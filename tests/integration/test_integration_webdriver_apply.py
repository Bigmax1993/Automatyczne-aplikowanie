"""Integracja: webdriver_apply — HTTP lokalny + fetch_html + extract_emails."""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

import webdriver_apply
from webdriver_apply import extract_emails, fetch_html


class _HtmlHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = (
            b"<!DOCTYPE html><html><body>"
            b'<a href="mailto:integration@local.test?subject=Hi">contact</a>'
            b" also jobs@local.test text"
            b"</body></html>"
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args, **kwargs) -> None:
        pass


@pytest.mark.integration
def test_fetch_and_extract_from_local_http_server() -> None:
    httpd = HTTPServer(("127.0.0.1", 0), _HtmlHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{port}/"
        html = fetch_html(url)
        assert html
        emails = extract_emails(html)
        assert "integration@local.test" in emails
        assert "jobs@local.test" in emails
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
