import os, json
import clr

dll_path = os.path.abspath("Microsoft.AnalysisServices.AdomdClient.dll")
conn_str = "Provider=MSOLEDBSQL.1;Data Source=ALITTLEDAISY;Password=khiem123!;User ID=sa;Initial Catalog=SSAS"