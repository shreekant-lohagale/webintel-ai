
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
from urllib.parse import urlsplit

HOST = "127.0.0.1"
PORT = 8765

COUNTS = defaultdict(int)
LOCK = Lock()


class MockHandler(BaseHTTPRequestHandler):

    def respond(self, status, body, headers=None):
        data = body.encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )
        self.send_header("Content-Length", str(len(data)))

        for key, value in (headers or {}).items():
            self.send_header(key, value)

        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path

        if path == "/robots.txt":
            self.respond(
                200,
                "User-agent: *\nAllow: /\n"
            )
            return

        with LOCK:
            COUNTS[path] += 1
            attempt = COUNTS[path]

        if path == "/unstable":
            if attempt <= 2:
                self.respond(503, "Temporary failure")
            else:
                self.respond(
                    200,
                    "<html><h1>Recovered successfully</h1></html>"
                )

        elif path == "/limited":
            if attempt == 1:
                self.respond(
                    429,
                    "Too many requests",
                    {"Retry-After": "2"}
                )
            else:
                self.respond(
                    200,
                    "<html><h1>Rate limit recovered</h1></html>"
                )

        elif path == "/blocked":
            self.respond(403, "Access denied")

        elif path == "/captcha":
            self.respond(
                200,
                "<html><h1>CAPTCHA required</h1></html>"
            )

        elif path == "/always-error":
            self.respond(500, "Persistent server failure")

        else:
            self.respond(404, "Not found")


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), MockHandler)

    print(f"Mock server: http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
