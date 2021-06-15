import http.server
from json import dumps, load, loads, JSONDecodeError
import socketserver
import argparse
from urllib.parse import parse_qs, urlparse, urlencode
import re
from typing import Dict


class S(http.server.BaseHTTPRequestHandler):
    ROUTES: Dict[str, Dict] = {}

    def _respond(self, text: str = None, data: dict = None, json: dict = None, status: int = 200,
                 content_type: str = None):

        if json:
            string = dumps(json) + "\n"
        elif data:
            string = urlencode(data)
        elif text:
            string = text

        response = bytes(string, 'utf-8')

        if not content_type:
            content_type = 'application/json; charset=utf-8'

        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers',
                         'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token, Authorization')
        self.send_header('Access-Control-Allow-Methods', 'HEAD,GET,PUT,DELETE,OPTIONS')
        self.send_header('Access-Control-Allow-Credentials', 'true')

        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'none'")
        self.send_header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload')
        self.send_header('Cache-Control', 'private, no-cache, no-store, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        # self.send_header("Connection", "keep-alive")

        if string:
            self.send_header("Content-Length", str(len(response)))

        self.end_headers()

        if string:
            s = re.sub(r'( )\1+', r'\1', string.replace("\n", " "))
            if len(s) > 300:
                s = s[:300] + " ...(very long)..."
            print("> RESPONSE (%s): %s" % (content_type, s))
            self.wfile.write(response)

    def _get_payload(self):
        content_str = self.rfile.read(int(self.headers['Content-Length']))

        if self.headers['Content-Type'] == "application/x-www-form-urlencoded":
            return parse_qs(content_str.decode("utf-8"))
        elif self.headers['Content-Type'] == "application/json":
            try:
                return loads(content_str.decode())
            except JSONDecodeError:
                self._respond(('{ "error": "Request content not valid JSON" }'), status=400)

        return None

    def do_HEAD(self):
        self._respond()

    def do_OPTIONS(self):
        self._respond()

    def _handle_request(self):
        print("++++++++++++++++++++++++++++")
        up = urlparse(self.path)
        path = up.path
        query = parse_qs(up.query)
        print(f"< Headers: {dict(self.headers)}")
        print(f"< Query: {query}")

        payload = None
        if self.command in ('POST', 'PUT', 'PATCH'):
            payload = self._get_payload()
            print(f"< Payload: {payload}")

        if path not in S.ROUTES[self.command]:
            self._respond(('{ "error": "Unknown path: \'' + path + '\'" }'))
            return
        path_routes = S.ROUTES[self.command][path]

        match = None
        for r in path_routes:
            skip = set()
            if 'skip' in r:
                skip = set(r['skip'])

            print(f"? Checking route with id: {r['id']}")
            if 'headers' in r:
                headers_ok = True
                for k, v in r['headers'].items():
                    if k not in self.headers or self.headers[k] != v:
                        print(f"  - Headers do not match")
                        headers_ok = False
                        break
                if not headers_ok:
                    continue
            if 'query' in r and query != r['query']:
                print(f"  - query is not equal")
                continue
            if self.headers['Content-Type'] == 'application/json' and ('json' not in r or payload != r['json']):
                if 'json' in skip:
                    print(f"  + json is not equal but route is defined to skip checking of json")
                else:
                    print(f"  - json is not equal")
                    continue
            elif self.headers['Content-Type'] == 'application/x-www-form-urlencoded' and \
                    ('data' not in r or payload != r['data']):
                print(f"  - data is not equal")
                continue
            match = r
            break

        if not match:
            self._respond(('{ "error": "Did not find a match" }'))
            return

        print(f"! Using route with id: {r['id']}")
        ret = match['return']
        ct = ret['content_type'] if 'content_type' in ret else None
        if 'json' in ret:
            self._respond(json=ret['json'], content_type=ct if ct else 'application/json')
        elif 'data' in ret:
            self._respond(data=ret['data'], content_type=ct if ct else 'application/x-www-form-urlencoded')
        elif 'text' in ret:
            self._respond(text=ret['text'], content_type=ct if ct else 'text/html')
        else:
            self._respond(('{ "error": "There is nothing to return (id: ' + r['id'] + ')" }'))

        print("----------------------------")

    def do_GET(self):
        self._handle_request()

    def do_PUT(self):
        self._handle_request()

    def do_POST(self):
        self._handle_request()


def run(handler_class=S, port=9876):
    httpd = socketserver.TCPServer(("", port), handler_class)
    print("! DP mock serving at port", port)
    httpd.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--routes', metavar='FILE', required=True, help='Routes json file')
    parser.add_argument('-p', '--port', default=9876, help='Port mock dp servers on')
    args, unknown = parser.parse_known_args()

    print(f"! Loading routes from {args.routes}")

    S.ROUTES = load(open(args.routes, "r", encoding='utf-8'))
    run(S, int(args.port))
