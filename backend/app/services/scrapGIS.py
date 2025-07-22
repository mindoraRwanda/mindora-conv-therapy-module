# import requests
# from bs4 import BeautifulSoup
# import re
# import json
# import pandas as pd
# import os

# # All dropdown dataset parameters
# map_types = {
#     "Pathologists_Per_Million": "n_path|min-max|1|1|1|Number of Pathologists Per Million Population",
#     "Pathology_Trainees": "n_trainees|min-max|1|1|1|Number of Pathology Trainees",
#     "Oncologists_Per_Million": "n_onco|min-max|1|1|1|Number of Oncologists Per Million Population",
#     "HistoCytotechnologists_Per_Million": "n_histocyto|min-max|1|1|1|Number of Histo/Cytotechnologists Per Million",
#     "Histotechnology_Trainees": "n_histotrainees|min-max|1|1|1|Number of Histotechnology Trainees",
#     "Cytotechnology_Trainees": "n_cytotrainees|min-max|1|1|1|Number of Cytotechnology Trainees",
#     "Small_Biopsies_Per_Year": "n_bx|min-max|1|1|1|Number of Small Biopsies (BX) Per Year",
#     "FNA_Per_Year": "n_fna|min-max|1|1|1|Number of Fine Needle Aspirations (FNA) Per Year",
#     "Total_Diagnostic_Procedures": "n_diag|min-max|1|1|1|Total Diagnostic Procedures Performed Per Year"
# }

# base_url = "https://www.pathologyinafrica.org/surveydata/map-data.php?type="

# def extract_map_data(full_url):
#     r = requests.get(full_url)
#     soup = BeautifulSoup(r.text, "html.parser")
#     scripts = soup.find_all("script")
#     for script in scripts:
#         if "var mapData" in script.text:
#             match = re.search(r"var mapData\s*=\s*(\{.*?\});", script.text, re.DOTALL)
#             if match:
#                 return json.loads(match.group(1))
#     return None

# # Create folder
# os.makedirs("pathology_data", exist_ok=True)

# # Download and save
# for label, param in map_types.items():
#     print(f"Processing: {label}")
#     data = extract_map_data(base_url + param)
#     if data:
#         df = pd.DataFrame([
#             {"Country": k, "Value": v.get("value", ""), "Color": v.get("color", "")}
#             for k, v in data.items()
#         ])
#         df.to_csv(f"pathology_data/{label}.csv", index=False)

# print("✅ All files saved in /pathology_data folder.")

