import os, json
import clr

dll_path = os.path.abspath("Microsoft.AnalysisServices.AdomdClient.dll")
clr.AddReference(dll_path)


from pyadomd import Pyadomd
from flask import Flask, jsonify, request

import requests

app = Flask(__name__)

conn_str = "Provider=MSOLEDBSQL.1;Data Source=ALITTLEDAISY;Password=khiem123!;User ID=sa;Initial Catalog=SSAS"
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

def fetch_schema(query):
    with Pyadomd(conn_str) as conn:
        with conn.cursor().execute(query) as cur:
            columns = [col[0] for col in cur.description]
            rows = cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]

def build_key_map():
    # Query các schema metadata
    dimensions = fetch_schema("SELECT * FROM $SYSTEM.MDSCHEMA_DIMENSIONS")
    hierarchies = fetch_schema("SELECT * FROM $SYSTEM.MDSCHEMA_HIERARCHIES")
    levels = fetch_schema("SELECT * FROM $SYSTEM.MDSCHEMA_LEVELS")

    key_map = {}

    for dim in dimensions:
        dim_name = dim.get('DIMENSION_UNIQUE_NAME')
        if not dim_name:
            continue
        # Lọc các hierarchies theo dimension
        dim_hierarchies = [h for h in hierarchies if h.get('DIMENSION_UNIQUE_NAME') == dim_name]
        for hier in dim_hierarchies:
            hier_name = hier.get('HIERARCHY_UNIQUE_NAME')
            if not hier_name:
                continue
            # Lọc các levels theo hierarchy
            hier_levels = [l for l in levels if l.get('HIERARCHY_UNIQUE_NAME') == hier_name]
            for level in hier_levels:
                level_name = level.get('LEVEL_UNIQUE_NAME')
                if not level_name:
                    continue
                # Tạo key như "[Dim Item].[Description].[Description].[MEMBER_CAPTION]"
                # lấy phần cuối của chuỗi DIMENSION, HIERARCHY, LEVEL để tạo key
                dim_key = dim_name
                hier_key = hier_name.split('.')[-1]
                level_key = level_name.split('.')[-1]
                key = f"{dim_key}.{hier_key}.{level_key}.[MEMBER_CAPTION]"
                value = level.get('LEVEL_CAPTION', '')
                key_map[key] = value

    return key_map

def save_key_map_to_json(key_map, filepath='./key_map.json'):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(key_map, f, ensure_ascii=False, indent=4)
    print(f"Saved key_map to {filepath}")

key_map = build_key_map()
save_key_map_to_json(key_map)

with Pyadomd(conn_str) as conn:
    mdx = "SELECT * FROM $SYSTEM.MDSCHEMA_MEASURES"
    with conn.cursor().execute(mdx) as cur:
        columns = [col[0] for col in cur.description]
        rows = cur.fetchall()
        measure_map = {}
        for row in rows:
            row_dict = dict(zip(columns, row))
            key = row_dict.get('MEASURE_UNIQUE_NAME')
            val = row_dict.get('MEASURE_CAPTION')
            if key and val:
                measure_map[key] = val

    print(measure_map)


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
