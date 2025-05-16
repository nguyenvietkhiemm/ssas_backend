import os, json
import clr
from config import conn_str, dll_path # cấu hình kết nối
import database # khởi chạy kết nối, tạo key_map, tên cột...

clr.AddReference(dll_path)

from pyadomd import Pyadomd
from flask import Flask, jsonify, request


app = Flask(__name__)

def load_key_map_from_json(filepath='./key_map.json'):
    with open(filepath, 'r', encoding='utf-8') as f:
        key_map = json.load(f)
    return key_map

key_map = load_key_map_from_json()

mdx_template = """
SELECT 
  NON EMPTY {{ [Measures].[Quantity] }} ON COLUMNS,
  SUBSET(
    {{
      NONEMPTY(
        [Dim Store].[Store ID].[Store ID].ALLMEMBERS *
        [Dim Store].[SCA].[State].ALLMEMBERS *
        [Dim Store].[City Name].[City Name].ALLMEMBERS *
        [Dim Store].[Phone].[Phone].ALLMEMBERS *
        [Dim Item].[Description].[Description].ALLMEMBERS *
        [Dim Item].[Size].[Size].ALLMEMBERS *
        [Dim Item].[Weight].[Weight].ALLMEMBERS *
        [Dim Item].[Price].[Price].ALLMEMBERS,
        [Measures].[Quantity]
      )
    }},
    {offset}, {limit}
  )
  DIMENSION PROPERTIES MEMBER_CAPTION, MEMBER_UNIQUE_NAME ON ROWS
FROM [Cube]
CELL PROPERTIES VALUE, BACK_COLOR, FORE_COLOR, FORMATTED_VALUE, FORMAT_STRING, FONT_NAME, FONT_SIZE, FONT_FLAGS
"""

mdx_template = """
SELECT 
  NON EMPTY {{ [Measures].[Total Amount] }} ON COLUMNS,

  SUBSET(
    {{
      NONEMPTY(
        [Dim Customer].[Customer ID].[Customer ID].ALLMEMBERS *
        [Fact Order].[Order ID].[Order ID].ALLMEMBERS *
        [Dim Customer].[Customer Name].[Customer Name].ALLMEMBERS *
        [Dim Time].[YQMD].[Day].ALLMEMBERS,
        [Measures].[Total Amount]
      )
    }},
    {offset}, {limit}
  )
  DIMENSION PROPERTIES MEMBER_CAPTION, MEMBER_UNIQUE_NAME ON ROWS

FROM [Cube]

CELL PROPERTIES VALUE, BACK_COLOR, FORE_COLOR, FORMATTED_VALUE, FORMAT_STRING, FONT_NAME, FONT_SIZE, FONT_FLAGS

"""

@app.route('/api')
def query():
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    
    mdx = mdx_template.format(limit=limit, offset=offset)
    
    results = []
    with Pyadomd(conn_str) as conn:
        with conn.cursor().execute(mdx) as cur:
            columns = [col[0] for col in cur.description]
            rows = cur.fetchall()
            for row in rows:
                row_dict = dict(zip(columns, row))
                short_dict = {}
                for k, v in row_dict.items():
                    if k in key_map:
                        short_dict[key_map[k]] = v
                results.append(short_dict)
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True, port=5000)