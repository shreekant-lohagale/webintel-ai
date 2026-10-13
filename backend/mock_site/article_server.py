
from datetime import datetime, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
from urllib.parse import urlsplit


HOST = "127.0.0.1"
PORT = 8766


class ArticleState:
    def __init__(self):
        self.version = 1
        self.lock = Lock()

    def advance(self):
        with self.lock:
            self.version += 1
            return self.version

    def current_version(self):
        with self.lock:
            return self.version


def build_handler(state):

    class ArticleHandler(BaseHTTPRequestHandler):

        def respond(self, status, body, content_type="text/html"):
            data = body.encode("utf-8")

            self.send_response(status)
            self.send_header(
                "Content-Type",
                f"{content_type}; charset=utf-8",
            )
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urlsplit(self.path).path

            if path == "/robots.txt":
                self.respond(
                    200,
                    "User-agent: *\nAllow: /\n",
                    "text/plain",
                )
                return

            if path == "/":
                self.respond(
                    200,
                    """
                    <html>
                    <head><title>WebIntel Test News</title></head>
                    <body>
                        <h1>WebIntel Test News</h1>
                        <a href="/articles/ai-workflows">
                            AI Workflows
                        </a>
                        <a href="/articles/data-engineering">
                            Data Engineering
                        </a>
                    </body>
                    </html>
                    """,
                )
                return

            articles = {
                "/articles/ai-workflows": {
                    "title": "AI Workflows in Modern Business",
                    "author": "WebIntel Test Editor",
                    "tags": "AI,Automation,Workflows",
                    "body": (
                        "Artificial intelligence is helping teams "
                        "organize information and improve workflows."
                    ),
                },
                "/articles/data-engineering": {
                    "title": "Reliable Data Engineering Pipelines",
                    "author": "WebIntel Research Desk",
                    "tags": "Data,Engineering,Python",
                    "body": (
                        "Reliable data pipelines combine extraction, "
                        "validation, provenance, and durable storage."
                    ),
                },
            }

            article = articles.get(path)

            if article is None:
                self.respond(404, "Not found")
                return

            version = state.current_version()

            body = article["body"]

            if (
                path == "/articles/ai-workflows"
                and version >= 2
            ):
                body += (
                    " The updated report also discusses "
                    "human review and measurable outcomes."
                )

            page = f"""
            <!doctype html>
            <html>
              <head>
                <title>{escape(article["title"])}</title>
                <meta name="author"
                      content="{escape(article["author"])}">
                <meta name="keywords"
                      content="{escape(article["tags"])}">
              </head>
              <body>
                <article>
                  <h1>{escape(article["title"])}</h1>
                  <time datetime="2026-10-13T08:00:00+00:00">
                    October 13, 2026
                  </time>
                  <div class="article-body">
                    <p>{escape(body)}</p>
                  </div>
                </article>
              </body>
            </html>
            """

            self.respond(200, page)

        def do_POST(self):
            if urlsplit(self.path).path != "/test/advance":
                self.respond(404, "Not found")
                return

            version = state.advance()

            self.respond(
                200,
                f'{{"version": {version}}}',
                "application/json",
            )

        def log_message(self, fmt, *args):
            print(
                "[ARTICLE MOCK] " + fmt % args,
                flush=True,
            )

    return ArticleHandler


def create_server(host=HOST, port=PORT):
    state = ArticleState()
    server = ThreadingHTTPServer(
        (host, port),
        build_handler(state),
    )
    return server


if __name__ == "__main__":
    server = create_server()

    print(
        f"Article mock server: http://{HOST}:{PORT}/",
        flush=True,
    )
    print("Press Ctrl+C to stop.", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
