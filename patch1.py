import re

p = "extract_crime_pdf.py"
s = open(p, encoding="utf-8").read()
s = s.replace(
    'if name.lower().startswith("total"):',
    "if is_total_row(name):",
)
helper = '''def is_total_row(name):
    n = name.lower()
    return "total" in n and ("district" in n or n.strip() == "total" or n.endswith("total"))


'''
s = s.replace("def cluster_bands(words, gap=10.0):", helper + "def cluster_bands(words, gap=10.0):")
open(p, "w", encoding="utf-8").write(s)
print("patched", s.count("is_total_row(name)"), "total checks")
