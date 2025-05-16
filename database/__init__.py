import os, json
import clr
from config import conn_str, dll_path

clr.AddReference(dll_path)

from pyadomd import Pyadomd

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
        dim_hierarchies = [h for h in hierarchies if h.get('DIMENSION_UNIQUE_NAME') == dim_name]
        for hier in dim_hierarchies:
            hier_name = hier.get('HIERARCHY_UNIQUE_NAME')
            if not hier_name:
                continue
            hier_levels = [l for l in levels if l.get('HIERARCHY_UNIQUE_NAME') == hier_name]
            for level in hier_levels:
                level_name = level.get('LEVEL_UNIQUE_NAME')
                if not level_name:
                    continue
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
    print(f"=== Saved key_map to {filepath} ===")

key_map = build_key_map()
save_key_map_to_json(key_map)