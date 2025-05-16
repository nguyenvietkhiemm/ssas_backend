import os
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

@app.route('/api')
def query():
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    
    mdx = mdx_template.format(limit=limit, offset=offset)
    
    results = []
    with Pyadomd(conn_str) as conn:
        with conn.cursor().execute(mdx) as cur:
            rows = cur.fetchall()
            for row in rows[:10]:
                results.append(list(row))
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
