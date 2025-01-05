import json
import pathlib
import mimetypes
import urllib.parse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("templates"))


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        elif pr_url.path == "/read":
            data = self.read_file()
            template = env.get_template("read.html")
            output = template.render(users=data)
            self.send_html_file_from_string(output)
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        data_parse = urllib.parse.unquote_plus(data.decode())
        timestamp = datetime.now().isoformat()
        data_dict = {
            timestamp: {
                key: value
                for key, value in [el.split("=") for el in data_parse.split("&")]
            }
        }
        self.write_to_file(data_dict)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_html_file(self, filename, status=200):
        try:
            self.send_response(status)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open(filename, "rb") as fd:
                self.wfile.write(fd.read())
        except FileNotFoundError:
            self.send_html_file("error.html", 404)

    def send_html_file_from_string(self, html_content, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())

    def read_file(self):
        try:
            with open("storage/data.json", "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    @staticmethod
    def write_to_file(content):
        try:
            with open("storage/data.json", "r+") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = {}

                data.update(content)

                file.seek(0)
                json.dump(data, file, indent=4)
        except FileNotFoundError:
            pathlib.Path("storage").mkdir(parents=True, exist_ok=True)
            with open("storage/data.json", "w", encoding="utf-8") as file:
                json.dump(content, file, indent=4)


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run()
