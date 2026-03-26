import json
import html
import gzip
import struct
import psycopg
from flask import Flask, Response, request
from time import perf_counter
from collections import OrderedDict

app = Flask(__name__)

cache = OrderedDict()
CACHE_MAX_SIZE = 100

DB_CONFIG = {
    "host": "localhost",
    "port": 9876,
    "dbname": "lego-db",
    "user": "lego",
    "password": "bricks",
}

class Database:
    def __init__(self):
        self.conn = psycopg.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
    
    def execute_and_fetch_all(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def close(self):
        self.cursor.close()
        self.conn.close()

        
@app.route("/")
def index():
    with open("templates/index.html") as f:
        template = f.read()
    return Response(template)

def get_sets_html(db, template, encoding):
    result = []
    rows = db.execute_and_fetch_all("select id, name from lego_set order by id")
    for row in rows:
        html_safe_id = html.escape(row[0])
        html_safe_name = html.escape(row[1])
        result.append(f'<tr><td><a href="/set?id={html_safe_id}">{html_safe_id}</a></td><td>{html_safe_name}</td></tr>\n')
    charset_tag = '<meta charset="UTF-8">' if encoding == "utf-8" else ""
    return template.replace("{ROWS}", "".join(result)).replace("{CHARSET}", charset_tag)

@app.route("/sets")
def sets():
    encoding = request.args.get("encoding", "utf-8")
    if encoding not in ("utf-8", "utf-16"):
        encoding = "utf-8"
    with open("templates/sets.html", "r", encoding="utf-8") as f:
        template = f.read()
    start_time = perf_counter()
    db = Database()
    try:
        page_html = get_sets_html(db, template, encoding)
    finally:
        db.close()
    print(f"Time to render all sets: {perf_counter() - start_time}")
    encoded_html = page_html.encode(encoding)
    compressed = gzip.compress(encoded_html)
    return Response(
        compressed,
        content_type=f"text/html; charset={encoding}",
        headers={"Content-Encoding": "gzip", "Cache-Control": "max-age=60"}
    )

@app.route("/set")
def legoSet():
    with open("templates/set.html") as f:
        template = f.read()
    return Response(template)

def get_set_data(db, set_id):
    if set_id in cache:
        cache.move_to_end(set_id)
        return json.dumps(cache[set_id], indent=4)
    
    row = db.execute_and_fetch_all("SELECT id, name, year, category FROM lego_set WHERE id = %s", (set_id,))
    rows = db.execute_and_fetch_all("SELECT brick_type_id, color_id, count FROM lego_inventory WHERE set_id = %s", (set_id,))
    
    result = {
        "id": row[0][0],
        "name": row[0][1],
        "year": row[0][2],
        "category": row[0][3],
        "inventory": [
            {"brick_type_id": r[0], "color_id": r[1], "count": r[2]}
            for r in rows
        ]
    }
    
    cache[set_id] = result
    if len(cache) > CACHE_MAX_SIZE:
        cache.popitem(last=False)
    
    return json.dumps(result, indent=4)

@app.route("/api/set")
def apiSet():
    set_id = request.args.get("id")
    db = Database()
    try:
        result = get_set_data(db, set_id)
    finally:
        db.close()
    return Response(result, content_type="application/json")

def get_set_binary(db, set_id):
    def write_string(s):
        encoded = s.encode("utf-8")
        return struct.pack(">H", len(encoded)) + encoded

    row = db.execute_and_fetch_all("SELECT id, name, year, category FROM lego_set WHERE id = %s", (set_id,))
    rows = db.execute_and_fetch_all("SELECT brick_type_id, color_id, count FROM lego_inventory WHERE set_id = %s", (set_id,))
    
    r = row[0]
    data = b""
    data += write_string(r[0])
    data += write_string(r[1])
    data += struct.pack(">H", r[2] if r[2] else 0)
    data += write_string(r[3] if r[3] else "")
    data += struct.pack(">I", len(rows))
    for brick in rows:
        data += write_string(brick[0])
        data += struct.pack(">H", brick[1])
        data += struct.pack(">H", brick[2])
    return data

@app.route("/api/set/binary")
def apiSetBinary():
    set_id = request.args.get("id")
    db = Database()
    try:
        data = get_set_binary(db, set_id)
    finally:
        db.close()
    return Response(data, content_type="application/octet-stream")


if __name__ == "__main__":
    app.run(port=5000, debug=True)