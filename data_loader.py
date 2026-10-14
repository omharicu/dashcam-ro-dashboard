"""
Data Loader & Sync Module for NHAI RO Dashboard.
Handles:
1. Live download from view-only Google Sheet export URL.
2. Fallback to local reference Excel workbook.
3. Fast Parquet caching for sub-millisecond query performance.
4. Data sanitization and standardizing RO/PIU names.
"""

import os
import re
import io
import datetime
import requests
import openpyxl
import pandas as pd

CACHE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_CACHE = os.path.join(CACHE_DIR, "data_cache_projects.parquet")
SURVEYS_CACHE = os.path.join(CACHE_DIR, "data_cache_surveys.parquet")
META_CACHE = os.path.join(CACHE_DIR, "data_cache_meta.json")
LOCAL_EXCEL = os.path.join(CACHE_DIR, "Dashcam_Project Tracking Sheet v1.xlsx")
DEFAULT_GSHEET_URL = "https://docs.google.com/spreadsheets/d/1IIC7n6Nk7--CUTYPKeMKLdm7q-mjsWZc3DMuv09r6X0/edit?usp=sharing"

def clean_ro(name):
    if not name or pd.isna(name):
        return "Unknown"
    name = str(name).strip()
    if "Lucknow" in name or name == "UP West (Lucknow)":
        return "UP West"
    if "Varanasi" in name or name == "UP East (Varanasi)":
        return "UP East"
    if name in ["Chittoor"]:
        return "Vijayawada"
    if name in ["Kerala"]:
        return "Thiruvananthapuram"
    return name

def clean_str(val):
    if val is None or pd.isna(val):
        return ""
    return str(val).strip()

def clean_date_str(val):
    if val is None or pd.isna(val):
        return ""
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.strftime("%d-%m-%Y")
    val_str = str(val).strip()
    if val_str.startswith("1900") or val_str.startswith("66") or val_str.startswith("67"):
        return ""
    return val_str[:10]

def extract_gsheet_id(url_or_id):
    if not url_or_id:
        return None
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url_or_id)
    if match:
        return match.group(1)
    if len(url_or_id) > 20 and "/" not in url_or_id:
        return url_or_id.strip()
    return None

def fetch_gsheet_bytes(sheet_id_or_url):
    sheet_id = extract_gsheet_id(sheet_id_or_url)
    if not sheet_id:
        raise ValueError(f"Invalid Google Sheet URL or ID: {sheet_id_or_url}")
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    resp = requests.get(export_url, timeout=60)
    resp.raise_for_status()
    return io.BytesIO(resp.content)

def parse_workbook(wb_or_file):
    """
    Parses workbook into cleaned projects and surveys DataFrames.
    """
    if isinstance(wb_or_file, (str, io.BytesIO)):
        wb = openpyxl.load_workbook(wb_or_file, read_only=True, data_only=True)
    else:
        wb = wb_or_file

    # 1. Project Details
    ws_p = wb["Project Details"]
    rows_p = list(ws_p.iter_rows(values_only=True))
    headers_p = [clean_str(c).replace("\n", " ") if c is not None else f"Col_{i}" for i, c in enumerate(rows_p[1])]
    df_p = pd.DataFrame(rows_p[2:], columns=headers_p)
    df_p = df_p[df_p["UPC Code"].notna() & (df_p["UPC Code"].astype(str).str.strip() != "")].copy()

    df_p["RO_Clean"] = df_p["RO Name"].apply(clean_ro)
    df_p["PIU_Clean"] = df_p["PIU Name"].apply(clean_str)
    df_p["Project_Name_Clean"] = df_p["Project Name"].apply(clean_str)
    df_p["NH_Number_Clean"] = df_p["NH  Number"].apply(clean_str) if "NH  Number" in df_p.columns else df_p.get("NH Number", "").apply(clean_str)
    df_p["Mode_Clean"] = df_p["Mode of Implementation"].apply(clean_str)
    df_p["Length_Km"] = pd.to_numeric(df_p["Project Length (km)"], errors="coerce").fillna(0.0)
    df_p["Lanes"] = df_p["No. of Lane(s)"].apply(clean_str)
    df_p["Contractor"] = df_p.get("Contractor/ Concessionaire", pd.Series([""]*len(df_p))).apply(clean_str)
    df_p["AE_IE"] = df_p.get("AE/IE Name", pd.Series([""]*len(df_p))).apply(clean_str)

    # 2. Master Survey Data
    ws_m = wb["Master Survey Data"]
    rows_m = list(ws_m.iter_rows(values_only=True))
    headers_m = [clean_str(c).replace("\n", " ") if c is not None else f"Col_{i}" for i, c in enumerate(rows_m[0])]
    df_m = pd.DataFrame(rows_m[1:], columns=headers_m[:len(rows_m[1])])
    df_m = df_m[df_m["UPC Code"].notna() & (df_m["UPC Code"].astype(str).str.strip() != "")].copy()

    df_m["RO_Clean"] = df_m["RO Name"].apply(clean_ro)
    df_m["PIU_Clean"] = df_m["PIU Name"].apply(clean_str)
    df_m["Survey_Week_Num"] = pd.to_numeric(df_m["Survey Week"], errors="coerce").fillna(0).astype(int)
    
    # Standardize survey status
    def norm_status(s):
        s = clean_str(s)
        if "#REF" in s or not s:
            return "Pending"
        if "Complete" in s:
            return "Complete"
        if "Cancel" in s:
            return "Cancelled"
        if "Sched" in s:
            return "Scheduled"
        return s

    df_m["Survey_Status_Clean"] = df_m["Survey Status"].apply(norm_status)
    df_m["Remarks_Clean"] = df_m["Remarks"].apply(clean_str)
    df_m["Scheduled_Date"] = df_m["Scheduled  Survey Date (DD/MM/YYYY)"].apply(clean_date_str) if "Scheduled  Survey Date (DD/MM/YYYY)" in df_m.columns else ""
    df_m["Actual_Date"] = df_m["Actual  Survey Completion Date (DD/MM/YYYY)"].apply(clean_date_str) if "Actual  Survey Completion Date (DD/MM/YYYY)" in df_m.columns else ""
    df_m["Raw_Data_Date"] = df_m["Raw Data Submission Date (DD/MM/YYYY)"].apply(clean_date_str) if "Raw Data Submission Date (DD/MM/YYYY)" in df_m.columns else ""
    df_m["Report_Date"] = df_m["Report Submission Actual Date (DD/MM/YYYY)"].apply(clean_date_str) if "Report Submission Actual Date (DD/MM/YYYY)" in df_m.columns else ""
    
    # Links
    df_m["Raw_Video_Link"] = df_m.get("Raw Video Link", pd.Series([""]*len(df_m))).apply(clean_str)
    df_m["Processed_Video_Link"] = df_m.get("Processed Video Link", pd.Series([""]*len(df_m))).apply(clean_str)
    df_m["Survey_Report_Link"] = df_m.get("Original Survey Report Link", pd.Series([""]*len(df_m))).apply(clean_str)
    df_m["Final_Report_Link"] = df_m.get("Final Survey Report Link", pd.Series([""]*len(df_m))).apply(clean_str)
    df_m["Assessed_Report_Link"] = df_m.get("Assessed Report Link", pd.Series([""]*len(df_m))).apply(clean_str)
    df_m["Survey_Form_Link"] = df_m.get("Survey Form Link", pd.Series([""]*len(df_m))).apply(clean_str)
    df_m["Discrepancy_Doc"] = df_m.get("Discrepancy  Document", pd.Series([""]*len(df_m))).apply(clean_str)

    # Actual Report Link: Pick Original Survey Report Link, or Final Report Link, or Assessed Report Link
    def pick_actual_report(r):
        for col in ["Original Survey Report Link", "Final Survey Report Link", "Assessed Report Link"]:
            val = str(r.get(col, "")).strip()
            if val and val.lower() not in ["none", "nan", "n/a", ""] and val.startswith("http"):
                return val
        return ""

    df_m["Actual_Report_Link"] = df_m.apply(pick_actual_report, axis=1)

    # Delays and quality
    df_m["Delay_D1"] = pd.to_numeric(df_m.get("Delay D1 (Days)"), errors="coerce").fillna(0).astype(int)
    df_m["Defects_Reported"] = pd.to_numeric(df_m.get("Defects Reported (#)"), errors="coerce").fillna(0).astype(int)
    df_m["Precision_Score"] = pd.to_numeric(df_m.get("Precision Score (%)"), errors="coerce").fillna(0.0)
    df_m["Recall_Score"] = pd.to_numeric(df_m.get("Recall  Score (%)"), errors="coerce").fillna(0.0)
    df_m["Report_Status"] = df_m.get("Report Submission Status", pd.Series([""]*len(df_m))).apply(clean_str)

    # Convert all object columns to clean strings to prevent any parquet serialization issues
    for c in df_p.columns:
        if df_p[c].dtype == "object":
            df_p[c] = df_p[c].astype(str)
    for c in df_m.columns:
        if df_m[c].dtype == "object":
            df_m[c] = df_m[c].astype(str)

    return df_p, df_m

def sync_data(gsheet_url_or_id=DEFAULT_GSHEET_URL, force_reload=False):
    """
    Syncs data from Google Sheet if provided, or from local Excel,
    and writes to the fast Parquet cache.
    """
    if not force_reload and os.path.exists(PROJECTS_CACHE) and os.path.exists(SURVEYS_CACHE):
        return pd.read_parquet(PROJECTS_CACHE), pd.read_parquet(SURVEYS_CACHE)

    print("Syncing data...")
    df_p, df_m = None, None
    if gsheet_url_or_id:
        try:
            print(f"Fetching from Google Sheet: {gsheet_url_or_id}")
            excel_stream = fetch_gsheet_bytes(gsheet_url_or_id)
            df_p, df_m = parse_workbook(excel_stream)
        except Exception as e:
            print(f"Warning: Could not fetch from Google Sheet ({e}). Falling back to local copy.")
    
    if df_p is None or df_m is None:
        print(f"Parsing local file: {LOCAL_EXCEL}")
        df_p, df_m = parse_workbook(LOCAL_EXCEL)

    df_p.to_parquet(PROJECTS_CACHE, index=False)
    df_m.to_parquet(SURVEYS_CACHE, index=False)
    
    # Save sync timestamp
    now_str = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
    try:
        import json
        with open(META_CACHE, "w") as f:
            json.dump({"last_sync": now_str}, f)
    except Exception:
        pass

    print(f"Successfully cached {len(df_p)} projects and {len(df_m)} survey records at {now_str}.")
    return df_p, df_m

def get_last_sync_time():
    try:
        import json
        if os.path.exists(META_CACHE):
            with open(META_CACHE, "r") as f:
                data = json.load(f)
                return data.get("last_sync", "")
    except Exception:
        pass
    return ""

def load_cached_data():
    """
    Fast load function. Reads Parquet cache in <30ms.
    If cache doesn't exist, builds it from the local Excel file.
    """
    if not (os.path.exists(PROJECTS_CACHE) and os.path.exists(SURVEYS_CACHE)):
        return sync_data()
    return pd.read_parquet(PROJECTS_CACHE), pd.read_parquet(SURVEYS_CACHE)

if __name__ == "__main__":
    df_p, df_m = sync_data(force_reload=True)
    print("Done! Projects:", len(df_p), "| Surveys:", len(df_m))

