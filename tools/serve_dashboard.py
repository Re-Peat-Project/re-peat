#!/usr/bin/env python3
"""Serve a folder over HTTP with byte-range support, for the national dashboard (its map layers are a PMTiles archive).

    python tools/serve_dashboard.py [FOLDER] [--port 8000]      # FOLDER defaults to reports/national_profile

Open http://localhost:8000/dashboard.html. A page opened from disk (file://) shows everything except the map layers, because
PMTiles reads the archive with Range requests. Any static host that supports Range (GitHub Pages, S3, nginx) works the same way.
"""
import argparse
import os
import re
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class RangeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().send_head()
        m = re.fullmatch(r"bytes=(\d*)-(\d*)", rng.strip())
        size = os.path.getsize(path)
        if not m or not (m.group(1) or m.group(2)):
            return super().send_head()
        a, b = m.groups()
        start, end = (size - int(b), size - 1) if not a else (int(a), int(b) if b else size - 1)
        end = min(end, size - 1)
        if start > end or start >= size:
            self.send_error(416, "Range not satisfiable")
            return None
        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self._left = end - start + 1
        return f

    def copyfile(self, source, outputfile):
        left = getattr(self, "_left", None)
        if left is None:
            return super().copyfile(source, outputfile)
        while left > 0:
            chunk = source.read(min(65536, left))
            if not chunk:
                break
            outputfile.write(chunk)
            left -= len(chunk)
        self._left = None

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", nargs="?", default=str(Path(os.environ.get("REPEAT_WORK", ".")) / "national_profile"))
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()
    ThreadingHTTPServer(("127.0.0.1", a.port), partial(RangeHandler, directory=a.folder)).serve_forever()


if __name__ == "__main__":
    main()
