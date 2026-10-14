import streamlit as st
import pandas as pd
import datetime
import io
import data_loader
import tokens

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

# Validate access
is_valid, role, ro_canonical = tokens.validate_access(ro_param, key_param, admin_param)

# Load data (cached)
@st.cache_data(ttl=3600)
def get_data():
    return data_loader.load_cached_data()

try:
    df_projects, df_surveys = get_data()
except Exception as e:
    st.error(f"Error loading project data: {e}")
    st.stop()

# Helper for export
def to_excel_download(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='NHAI_Data')
    return output.getvalue()


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
        st.info("Each Regional Office (RO) has a dedicated access link to view their projects. Please use the personalized link provided to your RO.")
        
        with st.expander("🔑 Direct Key / Admin Access", expanded=True):
            input_ro = st.selectbox("Select Your Regional Office", ["-- Select RO --"] + sorted(list(tokens.RO_TOKENS.keys())))
            input_key = st.text_input("Enter RO Access Key or Admin Key", type="password")
            
            if st.button("Access Dashboard", use_container_width=True):
                if input_key == tokens.ADMIN_KEY:
                    st.query_params["admin"] = "true"
                    st.query_params["key"] = input_key
                    st.rerun()
                elif input_ro in tokens.RO_TOKENS and tokens.RO_TOKENS[input_ro].upper() == input_key.strip().upper():
                    st.query_params["ro"] = input_ro
                    st.query_params["key"] = input_key
                    st.rerun()
                else:
                    st.error("Invalid RO or Access Key. Please check with NHAI Head Office.")
    st.stop()


# =========================================================================
# VIEW 2: ADMIN / HEAD OFFICE HUB
# =========================================================================
if role == "admin":
    st.markdown("""
    <div class="main-header">
        <h1>🛣️ NHAI Head Office - Master Administration Hub</h1>
        <p>Dashcam Survey System Monitoring & Regional Office Link Directory</p>
    </div>
    """, unsafe_allow_html=True)
    
    admin_tab1, admin_tab2, admin_tab3 = st.tabs([
        "🔗 24 RO Dedicated Links Directory", 
        "🔄 Live Google Sheet Sync", 
        "📊 All-RO Operational Overview"
    ])
    
    with admin_tab1:
        st.subheader("Regional Office Access Links")
        st.write("Share each personalized link with the respective RO Chief General Manager / Project Directors. Each link is hard-locked to that RO's projects only.")
        
        # Build links table
        base_url = "http://localhost:8501"  # Or deployed URL
        ro_rows = []
        for ro_name, key in sorted(tokens.RO_TOKENS.items()):
            ro_proj_count = len(df_projects[df_projects["RO_Clean"] == ro_name])
            ro_km = df_projects[df_projects["RO_Clean"] == ro_name]["Length_Km"].sum()
            full_link = f"{base_url}/?ro={ro_name.replace(' ', '+')}&key={key}"
            ro_rows.append({
                "Regional Office": f"RO {ro_name}",
                "Projects": ro_proj_count,
                "Total Length (Km)": f"{ro_km:.1f}",
                "Access Key": key,
                "Direct Link": full_link
            })
        
        df_ro_links = pd.DataFrame(ro_rows)
        
        # Display as table
        st.dataframe(
            df_ro_links,
            column_config={
                "Direct Link": st.column_config.LinkColumn("Click to Open RO View", display_text="Open RO Portal")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Download directory
        csv = df_ro_links.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Link Directory (CSV)", csv, "NHAI_RO_Portal_Links.csv", "text/csv")
        
    with admin_tab2:
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

    with admin_tab3:
        st.subheader("National Overview Across 24 ROs")
        ro_summary = df_projects.groupby("RO_Clean").agg(
            Projects=("UPC Code", "count"),
            PIUs=("PIU_Clean", lambda s: len(set(x for x in s if x))),
            Total_Km=("Length_Km", "sum")
        ).reset_index().rename(columns={"RO_Clean": "Regional Office"})
        st.dataframe(ro_summary, hide_index=True, use_container_width=True)
        
    st.stop()


# =========================================================================
# VIEW 3: STRICT RO-LEVEL OPERATIONAL DASHBOARD
# =========================================================================

# Strict query isolation: RO can ONLY see their own data
ro_name = ro_canonical
ro_projects = df_projects[df_projects["RO_Clean"] == ro_name].copy()
ro_surveys = df_surveys[df_surveys["RO_Clean"] == ro_name].copy()

# Header
st.markdown(f"""
<div class="main-header">
    <h1>🛣️ NHAI Regional Office: {ro_name.upper()}</h1>
    <p>Official Highway Dashcam Survey & Project Tracking System</p>
</div>
""", unsafe_allow_html=True)

# Top KPI Summary Cards
tot_projects = len(ro_projects)
tot_length = ro_projects["Length_Km"].sum()
unique_pius = sorted(list(set(ro_projects["PIU_Clean"].dropna().unique())))
all_weeks = sorted([int(w) for w in ro_surveys["Survey_Week_Num"].unique() if w > 0])
latest_week = max(all_weeks) if all_weeks else 1

# Latest week survey status counts
surveys_latest = ro_surveys[ro_surveys["Survey_Week_Num"] == latest_week]
completed_latest = len(surveys_latest[surveys_latest["Survey_Status_Clean"] == "Complete"])
cancelled_latest = len(surveys_latest[surveys_latest["Survey_Status_Clean"] == "Cancelled"])
pending_latest = len(surveys_latest[surveys_latest["Survey_Status_Clean"].isin(["Scheduled", "Pending"])])

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Assigned Projects</div>
        <div class="kpi-value">{tot_projects}</div>
        <div class="kpi-sub">{len(unique_pius)} PIUs under RO</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Total Highway Length</div>
        <div class="kpi-value">{tot_length:,.1f} km</div>
        <div class="kpi-sub">Jurisdiction stretch</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Week {latest_week} Completed</div>
        <div class="kpi-value" style="color: #28a745;">{completed_latest}</div>
        <div class="kpi-sub">Surveys completed this week</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Week {latest_week} Exceptions</div>
        <div class="kpi-value" style="color: {'#dc3545' if cancelled_latest > 0 else '#6c757d'};">{cancelled_latest} Cancelled</div>
        <div class="kpi-sub">{pending_latest} pending execution</div>
    </div>
    """, unsafe_allow_html=True)

# Sidebar Filters
st.sidebar.header(f"🔍 RO {ro_name} Filters")

# PIU Filter
selected_piu = st.sidebar.selectbox("Filter by PIU", ["All PIUs"] + unique_pius)

# Week Filter
week_options = ["All Weeks", f"Latest (Week {latest_week})"] + [f"Week {w}" for w in sorted(all_weeks, reverse=True)]
selected_week_str = st.sidebar.selectbox("Select Survey Week", week_options, index=1 if latest_week else 0)

# Status Filter
status_options = ["All Statuses", "Complete", "Cancelled", "Scheduled / Pending"]
selected_status = st.sidebar.selectbox("Survey Status", status_options)

# Search Bar
search_term = st.sidebar.text_input("Search (NH, Project, UPC)", "")

# Apply Filters to Surveys
filtered_surveys = ro_surveys.copy()

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
filtered_projects = ro_projects.copy()
if selected_piu != "All PIUs":
    filtered_projects = filtered_projects[filtered_projects["PIU_Clean"] == selected_piu]
if search_term.strip():
    term = search_term.strip().lower()
    filtered_projects = filtered_projects[
        filtered_projects["Project_Name_Clean"].str.lower().str.contains(term, na=False) |
        filtered_projects["UPC Code"].str.lower().str.contains(term, na=False) |
        filtered_projects["NH_Number_Clean"].str.lower().str.contains(term, na=False)
    ]

# Main Workspace Tabs
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
    st.subheader(f"Survey Status Tracker - RO {ro_name}")
    st.caption(f"Showing {len(filtered_surveys)} survey records based on current filters.")
    
    if filtered_surveys.empty:
        st.info("No survey records match the selected filters.")
    else:
        # Prepare clean display table
        display_surveys = filtered_surveys[[
            "UPC Code", "Project Name", "PIU_Clean", "Survey_Week_Num", 
            "Survey_Status_Clean", "Remarks_Clean", "Scheduled_Date", "Actual_Date",
            "Delay_D1", "Raw_Video_Link", "Processed_Video_Link", "Actual_Report_Link"
        ]].copy()
        
        display_surveys.columns = [
            "UPC Code", "Project Name", "PIU", "Week", 
            "Status", "Remarks / Cancellation Reason", "Scheduled Date", "Completed Date", 
            "Delay (Days)", "Raw Video", "Processed Video", "Survey Report"
        ]
        
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
# TAB 2: PROJECT MASTER INVENTORY
# -------------------------------------------------------------------------
with tab_projects:
    st.subheader(f"Project Master Directory - RO {ro_name}")
    st.caption(f"Total {len(filtered_projects)} projects registered under {ro_name}.")
    
    display_p = filtered_projects[[
        "UPC Code", "Project_Name_Clean", "NH_Number_Clean", "PIU_Clean", 
        "Length_Km", "Lanes", "Mode_Clean", "Contractor", "AE_IE"
    ]].copy()
    display_p.columns = [
        "UPC Code", "Project Name", "NH Number", "PIU", 
        "Length (km)", "Lanes", "Mode", "Contractor / Concessionaire", "Consultant (AE/IE)"
    ]
    
    st.dataframe(
        display_p,
        column_config={
            "Length (km)": st.column_config.NumberColumn(format="%.2f km")
        },
        hide_index=True,
        use_container_width=True
    )

# -------------------------------------------------------------------------
# TAB 3: CANCELLATIONS & FIELD ISSUES
# -------------------------------------------------------------------------
with tab_cancellations:
    st.subheader("Survey Cancellations & Field Bottlenecks")
    cancelled_df = filtered_surveys[filtered_surveys["Survey_Status_Clean"] == "Cancelled"]
    
    if cancelled_df.empty:
        st.success("🎉 No cancelled surveys under current filter selection!")
    else:
        st.warning(f"Found {len(cancelled_df)} cancelled survey legs.")
        
        st.write("**Affected Stretches & Cancellation Details**")
        st.dataframe(
            cancelled_df[["UPC Code", "Project Name", "PIU_Clean", "Survey_Week_Num", "Remarks_Clean"]].rename(
                columns={"PIU_Clean": "PIU", "Survey_Week_Num": "Week", "Remarks_Clean": "Official Reason"}
            ),
            hide_index=True,
            use_container_width=True
        )

# -------------------------------------------------------------------------
# TAB 4: EXPORT FOR REVIEW MEETINGS
# -------------------------------------------------------------------------
with tab_export:
    st.subheader("📥 Export Data for RO Weekly Review Meetings")
    st.write("Generate an official Excel or CSV report containing the filtered projects and survey status for review with PIUs and Concessionaires.")
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        excel_bytes = to_excel_download(filtered_surveys)
        st.download_button(
            label="📊 Download Survey Status (Excel .xlsx)",
            data=excel_bytes,
            file_name=f"NHAI_RO_{ro_name}_Survey_Report_{datetime.date.today().strftime('%d_%m_%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with col_e2:
        csv_bytes = filtered_surveys.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download Survey Status (CSV)",
            data=csv_bytes,
            file_name=f"NHAI_RO_{ro_name}_Survey_Report_{datetime.date.today().strftime('%d_%m_%Y')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# Footer
st.sidebar.markdown("---")
st.sidebar.caption(f"🔒 Session locked to RO: **{ro_name}**")
st.sidebar.caption("NHAI Dashcam Monitoring System v1.0")

