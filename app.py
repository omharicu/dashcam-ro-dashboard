import streamlit as st
import pandas as pd
import datetime
import io
import importlib
import data_loader
import tokens

importlib.reload(data_loader)
importlib.reload(tokens)

# Set page config
st.set_page_config(
    page_title="NHAI Dashcam Survey Portal",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom NHAI-style CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #0b3c5d 0%, #1d2731 100%);
        padding: 18px 24px;
        border-radius: 8px;
        color: white;
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: #f9ba32;
        font-size: 26px;
        margin: 0;
        font-weight: 700;
    }
    .main-header p {
        color: #e0e0e0;
        font-size: 14px;
        margin: 4px 0 0 0;
    }
    .kpi-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-left: 5px solid #0b3c5d;
        border-radius: 6px;
        padding: 14px 18px;
        text-align: center;
        margin-bottom: 10px;
    }
    .kpi-title {
        font-size: 13px;
        color: #6c757d;
        font-weight: 600;
        text-transform: uppercase;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 700;
        color: #1d2731;
        margin: 4px 0;
    }
    .kpi-sub {
        font-size: 11px;
        color: #888;
    }
    .status-badge-complete {
        background-color: #d4edda;
        color: #155724;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .status-badge-cancelled {
        background-color: #f8d7da;
        color: #721c24;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .status-badge-pending {
        background-color: #fff3cd;
        color: #856404;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# 1. Read URL Query Parameters
query_params = st.query_params
ro_param = query_params.get("ro", None)
key_param = query_params.get("key", None)
admin_param = query_params.get("admin", None)
zone_param = query_params.get("zone", None)

# Validate access
res = tokens.validate_access(
    ro_param=ro_param, key_param=key_param, admin_param=admin_param, zone_param=zone_param
)
if isinstance(res, (tuple, list)) and len(res) >= 4:
    is_valid, role, ro_canonical, zone_canonical = res[:4]
elif isinstance(res, (tuple, list)) and len(res) == 3:
    is_valid, role, ro_canonical = res
    zone_canonical = None
else:
    is_valid, role, ro_canonical, zone_canonical = False, "unauthorized", None, None

# Auto-sync cache every 15 minutes (900 seconds) from live Google Sheet
@st.cache_data(ttl=900)
def get_data():
    try:
        return data_loader.sync_data(force_reload=True)
    except Exception as e:
        return data_loader.load_cached_data()

try:
    df_projects, df_surveys = get_data()
except Exception as e:
    st.error(f"Error loading project data: {e}")
    st.stop()

# Ensure required columns exist even if loaded from an older cache
if "Actual_Report_Link" not in df_surveys.columns:
    def pick_report(r):
        for col in ["Original Survey Report Link", "Final Survey Report Link", "Assessed Report Link", "Final_Report_Link", "Survey_Report_Link"]:
            val = str(r.get(col, "")).strip()
            if val and val.lower() not in ["none", "nan", "n/a", ""] and val.startswith("http"):
                return val
        return ""
    df_surveys["Actual_Report_Link"] = df_surveys.apply(pick_report, axis=1)

for col in ["Raw_Video_Link", "Processed_Video_Link", "Actual_Report_Link", "Delay_D1"]:
    if col not in df_surveys.columns:
        df_surveys[col] = ""

# Helper for export
def to_excel_download(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='NHAI_Data')
    return output.getvalue()


# Helper to get base URL
def get_base_url():
    base_url = "https://dashcam-ro-dashboard-jqvfjynvuyc3djjrxadogf.streamlit.app"
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers") and st.context.headers:
            host = st.context.headers.get("Host") or st.context.headers.get("host")
            if host:
                proto = "http" if ("localhost" in host or "127.0.0.1" in host) else "https"
                base_url = f"{proto}://{host}"
    except Exception:
        pass
    return base_url


# =========================================================================
# VIEW 1: UNAUTHORIZED / LOGIN GATE
# =========================================================================
if not is_valid:
    st.markdown("""
    <div class="main-header">
        <h1>🛣️ National Highways Authority of India (NHAI)</h1>
        <p>Digital Assessment System (DAS) - Dashcam Survey & Project Tracking Portal</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.warning("🔒 **Restricted Access Portal**")
        st.info("Each Regional Office (RO) and Zone has a dedicated access link to view their projects. Please use the personalized link provided to your office.")
        
        with st.expander("🔑 Direct Key / Admin Access", expanded=True):
            access_level = st.radio("Select Portal Level", ["Regional Office (RO)", "National Zone", "Head Office Admin"], horizontal=True)
            
            if access_level == "Regional Office (RO)":
                input_ro = st.selectbox("Select Regional Office", ["-- Select RO --"] + sorted(list(tokens.RO_TOKENS.keys())))
                input_key = st.text_input("Enter RO Access Key", type="password")
                if st.button("Access RO Dashboard", use_container_width=True):
                    if input_ro in tokens.RO_TOKENS and tokens.RO_TOKENS[input_ro].upper() == input_key.strip().upper():
                        st.query_params["ro"] = input_ro
                        st.query_params["key"] = input_key
                        st.rerun()
                    else:
                        st.error("Invalid RO or Access Key.")
                        
            elif access_level == "National Zone":
                zone_choices = ["-- Select Zone --"] + [f"Zone {z} - {tokens.ZONE_INFO[z]['name']}" for z in sorted(tokens.ZONE_TOKENS.keys())]
                input_zone = st.selectbox("Select Zone", zone_choices)
                input_key = st.text_input("Enter Zone Access Key", type="password")
                if st.button("Access Zonal Dashboard", use_container_width=True):
                    z_code = input_zone.split()[1] if input_zone != "-- Select Zone --" else ""
                    if z_code in tokens.ZONE_TOKENS and tokens.ZONE_TOKENS[z_code].upper() == input_key.strip().upper():
                        st.query_params["zone"] = z_code
                        st.query_params["key"] = input_key
                        st.rerun()
                    else:
                        st.error("Invalid Zone or Access Key.")
            else:
                input_key = st.text_input("Enter Head Office Admin Key", type="password")
                if st.button("Access Admin Hub", use_container_width=True):
                    if input_key == tokens.ADMIN_KEY:
                        st.query_params["admin"] = "true"
                        st.query_params["key"] = input_key
                        st.rerun()
                    else:
                        st.error("Invalid Admin Key.")
    st.stop()


# =========================================================================
# VIEW 2: ADMIN / HEAD OFFICE HUB
# =========================================================================
if role == "admin":
    st.markdown("""
    <div class="main-header">
        <h1>🛣️ NHAI Head Office - Master Administration Hub</h1>
        <p>Dashcam Survey System Monitoring & Regional / Zonal Office Link Directory</p>
    </div>
    """, unsafe_allow_html=True)
    
    admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
        "🌐 5 Zone Dedicated Links",
        "📍 24 RO Dedicated Links", 
        "🔄 Live Google Sheet Sync", 
        "📊 All-RO Operational Overview"
    ])
    
    base_url = get_base_url()

    with admin_tab1:
        st.subheader("National Zone Access Links (5 Zones)")
        st.write("Share each personalized link with the respective Zonal CGMs and Executive Directors. Each link is hard-locked to that Zone's projects and Regional Offices.")
        
        zone_rows = []
        for z_code, z_key in sorted(tokens.ZONE_TOKENS.items()):
            z_meta = tokens.ZONE_INFO[z_code]
            z_proj_count = len(df_projects[df_projects["Zone"] == z_code])
            z_km = df_projects[df_projects["Zone"] == z_code]["Length_Km"].sum()
            full_link = f"{base_url}/?zone={z_code}&key={z_key}"
            zone_rows.append({
                "Zone": f"Zone {z_code}",
                "Zone Name": z_meta["name"],
                "Contracted DAS Vendor": z_meta["vendor"],
                "ROs Covered": ", ".join(z_meta["ros"]),
                "Projects": z_proj_count,
                "Length (Km)": f"{z_km:.1f}",
                "Access Key": z_key,
                "Direct Link": full_link
            })
            
        df_zone_links = pd.DataFrame(zone_rows)
        st.dataframe(
            df_zone_links,
            column_config={
                "Direct Link": st.column_config.LinkColumn("Click to Open Zone View", display_text="Open Zone Portal")
            },
            hide_index=True,
            use_container_width=True
        )
        csv_z = df_zone_links.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Zone Links (CSV)", csv_z, "NHAI_Zone_Portal_Links.csv", "text/csv")

    with admin_tab2:
        st.subheader("Regional Office Access Links (24 ROs)")
        st.write("Share each personalized link with the respective RO Chief General Manager / Project Directors. Each link is hard-locked to that RO's projects only.")
        
        ro_rows = []
        for ro_name_key, key in sorted(tokens.RO_TOKENS.items()):
            ro_proj_count = len(df_projects[df_projects["RO_Clean"] == ro_name_key])
            ro_km = df_projects[df_projects["RO_Clean"] == ro_name_key]["Length_Km"].sum()
            full_link = f"{base_url}/?ro={ro_name_key.replace(' ', '+')}&key={key}"
            ro_rows.append({
                "Regional Office": f"RO {ro_name_key}",
                "Projects": ro_proj_count,
                "Total Length (Km)": f"{ro_km:.1f}",
                "Access Key": key,
                "Direct Link": full_link
            })
        
        df_ro_links = pd.DataFrame(ro_rows)
        st.dataframe(
            df_ro_links,
            column_config={
                "Direct Link": st.column_config.LinkColumn("Click to Open RO View", display_text="Open RO Portal")
            },
            hide_index=True,
            use_container_width=True
        )
        csv_ro = df_ro_links.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download RO Links (CSV)", csv_ro, "NHAI_RO_Portal_Links.csv", "text/csv")
        
    with admin_tab3:
        st.subheader("Live Google Sheet Connection (View-Only)")
        st.write("Enter the URL or Spreadsheet ID of the view-only Google Sheet to sync the latest weekly records.")
        
        gsheet_input = st.text_input(
            "Google Sheet URL or Spreadsheet ID",
            value=data_loader.DEFAULT_GSHEET_URL,
            placeholder="https://docs.google.com/spreadsheets/d/1.../edit?usp=sharing"
        )
        
        if st.button("🔄 Sync Live Data Now", type="primary"):
            if not gsheet_input.strip():
                st.warning("Please enter a Google Sheet URL or ID.")
            else:
                with st.spinner("Downloading and caching latest data from Google Sheet..."):
                    try:
                        df_p_new, df_m_new = data_loader.sync_data(gsheet_url_or_id=gsheet_input.strip(), force_reload=True)
                        st.cache_data.clear()
                        st.success(f"Successfully synced! Loaded {len(df_p_new)} projects and {len(df_m_new)} survey records.")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Failed to sync from Google Sheet: {err}")
                        
        st.divider()
        if st.button("↺ Reload from Local Backup Sheet"):
            with st.spinner("Reloading local reference sheet..."):
                data_loader.sync_data(force_reload=True)
                st.cache_data.clear()
                st.success("Local data reloaded!")
                st.rerun()

    with admin_tab4:
        st.subheader("National Overview Across 24 ROs")
        ro_summary = df_projects.groupby("RO_Clean").agg(
            Projects=("UPC Code", "count"),
            PIUs=("PIU_Clean", lambda s: len(set(x for x in s if x))),
            Total_Km=("Length_Km", "sum")
        ).reset_index().rename(columns={"RO_Clean": "Regional Office"})
        st.dataframe(ro_summary, hide_index=True, use_container_width=True)
        
    st.stop()


# =========================================================================
# VIEW 3: STRICT OPERATIONAL DASHBOARD (RO OR ZONE LEVEL)
# =========================================================================

is_zone = (role == "zone")
scope_zone = zone_canonical if is_zone else None
ro_name = ro_canonical if not is_zone else None

if is_zone:
    zone_info = tokens.ZONE_INFO.get(scope_zone, {})
    portal_title = f"Zone {scope_zone} - {zone_info.get('name', '')}"
    portal_subtitle = f"Contracted DAS Vendor: {zone_info.get('vendor', 'N/A')} | Highway Dashcam Survey & Project Tracking System"
    scope_projects = df_projects[df_projects["Zone"] == scope_zone].copy()
    scope_surveys = df_surveys[df_surveys["Zone"] == scope_zone].copy()
else:
    portal_title = f"Regional Office: {ro_name.upper() if ro_name else 'PORTAL'}"
    portal_subtitle = "Highway Dashcam Survey & Project Tracking System"
    scope_projects = df_projects[df_projects["RO_Clean"] == ro_name].copy() if ro_name else pd.DataFrame()
    scope_surveys = df_surveys[df_surveys["RO_Clean"] == ro_name].copy() if ro_name else pd.DataFrame()

# Header
st.markdown(f"""
<div class="main-header">
    <h1>🛣️ NHAI {portal_title}</h1>
    <p>{portal_subtitle}</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Filters
sidebar_title = f"🔍 Zone {scope_zone} Filters" if is_zone else f"🔍 RO {ro_name} Filters"
st.sidebar.header(sidebar_title)

# If Zone view, allow filtering by RO within that zone
selected_ro = "All ROs"
if is_zone:
    zone_ros = sorted(list(scope_projects["RO_Clean"].dropna().unique()))
    selected_ro = st.sidebar.selectbox("Filter by Regional Office (RO)", ["All ROs in Zone"] + zone_ros)
    if selected_ro != "All ROs in Zone":
        scope_projects = scope_projects[scope_projects["RO_Clean"] == selected_ro]
        scope_surveys = scope_surveys[scope_surveys["RO_Clean"] == selected_ro]

# PIU Filter
unique_pius = sorted(list(set(scope_projects["PIU_Clean"].dropna().unique())))
selected_piu = st.sidebar.selectbox("Filter by PIU", ["All PIUs"] + unique_pius)

# Week Filter
all_weeks = sorted([int(w) for w in scope_surveys["Survey_Week_Num"].unique() if w > 0])
latest_week = max(all_weeks) if all_weeks else 1
week_options = ["All Weeks", f"Latest (Week {latest_week})"] + [f"Week {w}" for w in sorted(all_weeks, reverse=True)]
selected_week_str = st.sidebar.selectbox("Select Survey Week", week_options, index=1 if latest_week else 0)

# Status Filter
status_options = ["All Statuses", "Complete", "Cancelled", "Scheduled / Pending"]
selected_status = st.sidebar.selectbox("Survey Status", status_options)

# Search Bar
search_term = st.sidebar.text_input("Search (NH, Project, UPC)", "")

# Apply Filters to Surveys
filtered_surveys = scope_surveys.copy()

if selected_piu != "All PIUs":
    filtered_surveys = filtered_surveys[filtered_surveys["PIU_Clean"] == selected_piu]

if selected_week_str == f"Latest (Week {latest_week})":
    filtered_surveys = filtered_surveys[filtered_surveys["Survey_Week_Num"] == latest_week]
elif selected_week_str != "All Weeks":
    w_num = int(selected_week_str.replace("Week ", ""))
    filtered_surveys = filtered_surveys[filtered_surveys["Survey_Week_Num"] == w_num]

if selected_status == "Complete":
    filtered_surveys = filtered_surveys[filtered_surveys["Survey_Status_Clean"] == "Complete"]
elif selected_status == "Cancelled":
    filtered_surveys = filtered_surveys[filtered_surveys["Survey_Status_Clean"] == "Cancelled"]
elif selected_status == "Scheduled / Pending":
    filtered_surveys = filtered_surveys[filtered_surveys["Survey_Status_Clean"].isin(["Scheduled", "Pending"])]

if search_term.strip():
    term = search_term.strip().lower()
    filtered_surveys = filtered_surveys[
        filtered_surveys["Project Name"].str.lower().str.contains(term, na=False) |
        filtered_surveys["UPC Code"].str.lower().str.contains(term, na=False) |
        filtered_surveys["Remarks_Clean"].str.lower().str.contains(term, na=False)
    ]

# Apply Filters to Projects Master
filtered_projects = scope_projects.copy()
if selected_piu != "All PIUs":
    filtered_projects = filtered_projects[filtered_projects["PIU_Clean"] == selected_piu]
if search_term.strip():
    term = search_term.strip().lower()
    filtered_projects = filtered_projects[
        filtered_projects["Project_Name_Clean"].str.lower().str.contains(term, na=False) |
        filtered_projects["UPC Code"].str.lower().str.contains(term, na=False) |
        filtered_projects["NH_Number_Clean"].str.lower().str.contains(term, na=False)
    ]

# Dynamic KPI Summary Cards (Reflects Active Filters)
card_projects = len(filtered_projects)
card_length = filtered_projects["Length_Km"].sum()
card_pius_count = filtered_projects["PIU_Clean"].nunique()

card_completed = len(filtered_surveys[filtered_surveys["Survey_Status_Clean"] == "Complete"])
card_cancelled = len(filtered_surveys[filtered_surveys["Survey_Status_Clean"] == "Cancelled"])
card_pending = len(filtered_surveys[filtered_surveys["Survey_Status_Clean"].isin(["Scheduled", "Pending"])])

if is_zone and selected_ro == "All ROs in Zone":
    scope_sub = f"{len(scope_projects['RO_Clean'].unique())} ROs | {card_pius_count} PIUs"
else:
    scope_sub = f"{card_pius_count} PIU(s)" if selected_piu == "All PIUs" else f"PIU: {selected_piu}"

week_sub = selected_week_str

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Projects</div>
        <div class="kpi-value">{card_projects}</div>
        <div class="kpi-sub">{scope_sub}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Highway Length</div>
        <div class="kpi-value">{card_length:,.1f} km</div>
        <div class="kpi-sub">Filtered stretch</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Surveys Completed</div>
        <div class="kpi-value" style="color: #28a745;">{card_completed}</div>
        <div class="kpi-sub">{week_sub}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Exceptions / Pending</div>
        <div class="kpi-value" style="color: {'#dc3545' if card_cancelled > 0 else '#6c757d'};">{card_cancelled} Cancelled</div>
        <div class="kpi-sub">{card_pending} pending execution</div>
    </div>
    """, unsafe_allow_html=True)

# Main Workspace Tabs
if is_zone:
    tab_surveys, tab_ro_breakdown, tab_projects, tab_cancellations, tab_export = st.tabs([
        f"📋 Weekly Survey Status ({len(filtered_surveys)})",
        f"🏢 RO Performance Breakdown",
        f"🛣️ Project Master Inventory ({len(filtered_projects)})",
        f"⚠️ Cancellations & Issues",
        "📥 Export for Review Meetings"
    ])
else:
    tab_surveys, tab_projects, tab_cancellations, tab_export = st.tabs([
        f"📋 Weekly Survey Status ({len(filtered_surveys)})",
        f"🛣️ Project Master Inventory ({len(filtered_projects)})",
        f"⚠️ Cancellations & Issues",
        "📥 Export for Review Meetings"
    ])

# -------------------------------------------------------------------------
# TAB 1: WEEKLY SURVEY TRACKER
# -------------------------------------------------------------------------
with tab_surveys:
    st.subheader(f"Survey Status Tracker - {portal_title}")
    st.caption(f"Showing {len(filtered_surveys)} survey records based on current filters.")
    
    if filtered_surveys.empty:
        st.info("No survey records match the selected filters.")
    else:
        # Prepare clean display table defensively
        survey_cols = [
            "UPC Code", "Project Name", "RO_Clean", "PIU_Clean", "Survey_Week_Num", 
            "Survey_Status_Clean", "Remarks_Clean", "Scheduled_Date", "Actual_Date",
            "Delay_D1", "Raw_Video_Link", "Processed_Video_Link", "Actual_Report_Link"
        ]
        for c in survey_cols:
            if c not in filtered_surveys.columns:
                filtered_surveys[c] = ""
                
        display_surveys = filtered_surveys[survey_cols].copy()
        
        display_surveys.columns = [
            "UPC Code", "Project Name", "RO", "PIU", "Week", 
            "Status", "Remarks / Cancellation Reason", "Scheduled Date", "Completed Date", 
            "Delay (Days)", "Raw Video", "Processed Video", "Survey Report"
        ]
        
        # If single RO, drop RO column for brevity
        if not is_zone or selected_ro != "All ROs in Zone":
            display_surveys = display_surveys.drop(columns=["RO"])
            
        st.dataframe(
            display_surveys,
            column_config={
                "Raw Video": st.column_config.LinkColumn("Raw Video", display_text="📹 Watch Video"),
                "Processed Video": st.column_config.LinkColumn("Processed Video", display_text="🎥 AI Viewer"),
                "Survey Report": st.column_config.LinkColumn("Survey Report", display_text="📄 View Report"),
                "Week": st.column_config.NumberColumn(format="%d"),
                "Delay (Days)": st.column_config.NumberColumn(format="%d d")
            },
            hide_index=True,
            use_container_width=True
        )

# -------------------------------------------------------------------------
# TAB: RO BREAKDOWN (ZONE VIEW ONLY)
# -------------------------------------------------------------------------
if is_zone:
    with tab_ro_breakdown:
        st.subheader(f"Regional Office Performance Comparison - Zone {scope_zone}")
        st.caption(f"Comparison across all Regional Offices in {zone_info.get('name')}.")
        
        ro_stats = []
        for r_name in sorted(scope_projects["RO_Clean"].unique()):
            r_projs = scope_projects[scope_projects["RO_Clean"] == r_name]
            r_survs = scope_surveys[scope_surveys["RO_Clean"] == r_name]
            
            p_cnt = len(r_projs)
            km_tot = r_projs["Length_Km"].sum()
            surv_tot = len(r_survs)
            comp_cnt = len(r_survs[r_survs["Survey_Status_Clean"] == "Complete"])
            canc_cnt = len(r_survs[r_survs["Survey_Status_Clean"] == "Cancelled"])
            pend_cnt = len(r_survs[r_survs["Survey_Status_Clean"].isin(["Scheduled", "Pending"])])
            comp_pct = (comp_cnt / surv_tot * 100) if surv_tot > 0 else 0
            
            ro_stats.append({
                "Regional Office": f"RO {r_name}",
                "Projects": p_cnt,
                "Length (km)": f"{km_tot:,.1f}",
                "Total Scheduled Surveys": surv_tot,
                "Completed Surveys": comp_cnt,
                "Completion Rate": f"{comp_pct:.1f}%",
                "Cancelled": canc_cnt,
                "Pending / Scheduled": pend_cnt
            })
            
        df_ro_stats = pd.DataFrame(ro_stats)
        st.dataframe(df_ro_stats, hide_index=True, use_container_width=True)

# -------------------------------------------------------------------------
# TAB: PROJECT MASTER INVENTORY
# -------------------------------------------------------------------------
with tab_projects:
    st.subheader(f"Project Master Directory - {portal_title}")
    st.caption(f"Total {len(filtered_projects)} projects registered.")
    
    proj_cols = [
        "UPC Code", "Project_Name_Clean", "NH_Number_Clean", "RO_Clean", "PIU_Clean", 
        "Length_Km", "Lanes", "Mode_Clean", "Contractor", "AE_IE"
    ]
    for c in proj_cols:
        if c not in filtered_projects.columns:
            filtered_projects[c] = ""
            
    display_p = filtered_projects[proj_cols].copy()
    display_p.columns = [
        "UPC Code", "Project Name", "NH Number", "RO", "PIU", 
        "Length (km)", "Lanes", "Mode", "Contractor / Concessionaire", "Consultant (AE/IE)"
    ]
    
    if not is_zone or selected_ro != "All ROs in Zone":
        display_p = display_p.drop(columns=["RO"])
        
    st.dataframe(
        display_p,
        column_config={
            "Length (km)": st.column_config.NumberColumn(format="%.2f km")
        },
        hide_index=True,
        use_container_width=True
    )

# -------------------------------------------------------------------------
# TAB: CANCELLATIONS & FIELD ISSUES
# -------------------------------------------------------------------------
with tab_cancellations:
    st.subheader("Survey Cancellations & Field Bottlenecks")
    cancelled_df = filtered_surveys[filtered_surveys["Survey_Status_Clean"] == "Cancelled"]
    
    if cancelled_df.empty:
        st.success("🎉 No cancelled surveys under current filter selection!")
    else:
        st.warning(f"Found {len(cancelled_df)} cancelled survey legs.")
        
        st.write("**Affected Stretches & Cancellation Details**")
        canc_cols = ["UPC Code", "Project Name", "RO_Clean", "PIU_Clean", "Survey_Week_Num", "Remarks_Clean"]
        for c in canc_cols:
            if c not in cancelled_df.columns:
                cancelled_df[c] = ""
                
        disp_canc = cancelled_df[canc_cols].copy()
        disp_canc.columns = ["UPC Code", "Project Name", "RO", "PIU", "Week", "Reason / Remarks"]
        if not is_zone or selected_ro != "All ROs in Zone":
            disp_canc = disp_canc.drop(columns=["RO"])
            
        st.dataframe(
            disp_canc,
            hide_index=True,
            use_container_width=True
        )

# -------------------------------------------------------------------------
# TAB: EXPORT FOR REVIEW MEETINGS
# -------------------------------------------------------------------------
with tab_export:
    st.subheader("📥 Export Data for Review Meetings")
    st.write("Generate an Excel or CSV report containing the filtered projects and survey status for review.")
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        excel_bytes = to_excel_download(filtered_surveys)
        export_tag = f"Zone_{scope_zone}" if is_zone else f"RO_{ro_name}"
        st.download_button(
            label="📊 Download Survey Status (Excel .xlsx)",
            data=excel_bytes,
            file_name=f"NHAI_{export_tag}_Survey_Report_{datetime.date.today().strftime('%d_%m_%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with col_e2:
        csv_bytes = filtered_surveys.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download Survey Status (CSV)",
            data=csv_bytes,
            file_name=f"NHAI_{export_tag}_Survey_Report_{datetime.date.today().strftime('%d_%m_%Y')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# Footer
st.sidebar.markdown("---")
last_sync = data_loader.get_last_sync_time()
if last_sync:
    st.sidebar.caption(f"🕒 **Last Synced**: {last_sync}")

if st.sidebar.button("🔄 Sync Latest Sheet Updates", use_container_width=True):
    with st.spinner("Fetching latest updates from Google Sheet..."):
        st.cache_data.clear()
        get_data()
    st.success("Synced!")
    st.rerun()

session_scope = f"Zone: **Zone {scope_zone}**" if is_zone else f"RO: **{ro_name}**"
st.sidebar.caption(f"🔒 Session locked to {session_scope}")
st.sidebar.caption("NHAI Dashcam Monitoring System v1.0")
