import pandas as pd
import re
import os
import glob

base = os.path.dirname(os.path.abspath(__file__))
csv_files = glob.glob(os.path.join(base, "*.csv"))
src = [f for f in csv_files if "feedback" in f.lower() and "cleaned" not in f.lower()][0]
print(f"Reading: {src}")

df = pd.read_csv(src, encoding="utf-8")

def normalize_date(d):
    d = str(d).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        return d
    if re.match(r"^\d{4}/\d{2}/\d{2}$", d):
        return d.replace("/", "-")
    m = re.match(r"^(\d{1,2})월\s*(\d{1,2})일$", d)
    if m:
        return f"2026-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    m = re.match(r"^(\d{2})\.(\d{1,2})\.(\d{1,2})$", d)
    if m:
        return f"20{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return d

df["받은날짜"] = df["받은날짜"].apply(normalize_date)
out = os.path.join(base, "feedback_cleaned.csv")
df.to_csv(out, index=False, encoding="utf-8-sig")
print("날짜 통일 완료:")
print(df[["id", "받은날짜", "별점"]].to_string(index=False))
