from flask import Flask, jsonify, request
from pyadomd import Pyadomd
import os
import json
import clr
from config import conn_str, dll_path, key_map  # cấu hình kết nối
import database  # khởi chạy kết nối, tạo key_map, tên cột...
from flask_cors import CORS

from config import generate_mdx  # cấu hình kết nối

clr.AddReference(dll_path)

app = Flask(__name__)
CORS(app)  # Cho phép tất cả domain truy cập (hoặc tùy chỉnh origin)

@app.route('/api')
def query():
    dimensions = ["Customer ID", "Customer Name", "City Name", "Day", "Order ID"]
    dimensions = request.args.getlist('dimensions')
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))

    mdx = generate_mdx(dimensions=dimensions,
                       limit=limit, 
                       offset=offset)

    results = []
    with Pyadomd(conn_str) as conn:
        with conn.cursor().execute(mdx) as cur:
            columns = [col[0] for col in cur.description]
            rows = cur.fetchall()
            for row in rows:
                row_dict = dict(zip(columns, row))
                short_dict = {}
                for k, v in row_dict.items():
                    # Bỏ .[MEMBER_CAPTION] nếu có
                    clean_key = k.replace(".[MEMBER_CAPTION]", "")
                    if clean_key in key_map:
                        short_dict[key_map[clean_key]] = v
                results.append(short_dict)
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
