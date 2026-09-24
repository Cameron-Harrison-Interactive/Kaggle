import datetime
import http.server

LOG = "/home/user/war/oauth_callback.log"


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        with open(LOG, "a") as f:
            f.write(f"{datetime.datetime.utcnow().isoformat()}Z {self.path}\n")
        ok = "code=" in self.path
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        if ok:
            body = (b"<html><body style='font-family:sans-serif;background:#0f172a;color:#e2e8f0;"
                    b"display:flex;align-items:center;justify-content:center;height:100vh;margin:0'>"
                    b"<div style='text-align:center'><h1>&#9989; Code captured</h1>"
                    b"<p>The agent can finish the submission now &mdash; close this tab.</p></div></body></html>")
        else:
            body = (b"<html><body style='font-family:sans-serif'><h2>OAuth trap listening.</h2>"
                    b"<p>Waiting for the Kaggle redirect...</p></body></html>")
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    http.server.HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
