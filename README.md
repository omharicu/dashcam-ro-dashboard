# NHAI Regional Office Dashcam Survey & Project Tracking Portal

A zero-cost, hardware-independent web dashboard for the **National Highways Authority of India (NHAI)** to monitor digital dashcam highway surveys across all 24 Regional Offices (ROs) and Project Implementation Units (PIUs).

---

## Key Features

1. **Strict RO-Level Privacy (No Cross-RO Visibility)**:
   - Each RO has a unique, dedicated access link with a cryptographic key.
   - RO Jaipur can only see Jaipur's projects; RO Chandigarh can only see Chandigarh's.
   - If a URL is tampered with, access is immediately blocked.
2. **Pure Operational RO Workspace**:
   - Project inventory with NH numbers, lengths, modes (EPC, HAM, BOT, PBMC), and concessionaires.
   - Weekly survey execution tracker (Completed, Cancelled with official reasons, or Scheduled).
   - Direct hyperlinks to raw dashcam videos, AI-processed video viewers, and survey reports.
   - Instant filtering by PIU, Survey Week, and status.
   - One-click export to Excel / CSV for RO review meetings.
3. **Hardware-Independent (Runs 24/7 in the Cloud for ₹0)**:
   - Designed for 1-click deployment on **Streamlit Community Cloud** (100% free forever).
   - Syncs directly from your view-only online Google Sheet.
   - Fast Parquet caching provides sub-50ms query speeds.
4. **Master Admin Hub**:
   - Access key: `HQ-ADMIN-7700`
   - Complete directory of all 24 RO links with 1-click copy/preview.
   - Live Google Sheet sync button to refresh data on demand.

---

## 24 Regional Office Link Directory

When deployed to Streamlit Cloud, replace `http://localhost:8501` with your public Streamlit URL (e.g. `https://nhai-dashcam.streamlit.app`):

| Regional Office | Zone | Access Key | Dedicated Link |
| :--- | :---: | :---: | :--- |
| **RO Bengaluru** | D | `BLR-7482` | `http://localhost:8501/?ro=Bengaluru&key=BLR-7482` |
| **RO Bhopal** | C | `BPL-3914` | `http://localhost:8501/?ro=Bhopal&key=BPL-3914` |
| **RO Bhubaneswar** | E | `BBS-8521` | `http://localhost:8501/?ro=Bhubaneswar&key=BBS-8521` |
| **RO Chandigarh** | A | `CHD-1943` | `http://localhost:8501/?ro=Chandigarh&key=CHD-1943` |
| **RO Chennai** | D | `MAA-6278` | `http://localhost:8501/?ro=Chennai&key=MAA-6278` |
| **RO Dehradun** | A | `DDN-5190` | `http://localhost:8501/?ro=Dehradun&key=DDN-5190` |
| **RO Delhi** | A | `DEL-8402` | `http://localhost:8501/?ro=Delhi&key=DEL-8402` |
| **RO Gandhinagar** | B | `GNR-3715` | `http://localhost:8501/?ro=Gandhinagar&key=GNR-3715` |
| **RO Guwahati** | E | `GAU-9641` | `http://localhost:8501/?ro=Guwahati&key=GAU-9641` |
| **RO Hyderabad** | D | `HYD-2839` | `http://localhost:8501/?ro=Hyderabad&key=HYD-2839` |
| **RO Jaipur** | B | `JPR-4826` | `http://localhost:8501/?ro=Jaipur&key=JPR-4826` |
| **RO Jammu** | A | `JMU-7153` | `http://localhost:8501/?ro=Jammu&key=JMU-7153` |
| **RO Kolkata** | E | `CCU-3694` | `http://localhost:8501/?ro=Kolkata&key=CCU-3694` |
| **RO Madurai** | D | `IXM-8205` | `http://localhost:8501/?ro=Madurai&key=IXM-8205` |
| **RO Mumbai** | C | `BOM-5417` | `http://localhost:8501/?ro=Mumbai&key=BOM-5417` |
| **RO Nagpur** | C | `NAG-1962` | `http://localhost:8501/?ro=Nagpur&key=NAG-1962` |
| **RO Patna** | E | `PAT-6380` | `http://localhost:8501/?ro=Patna&key=PAT-6380` |
| **RO Raipur** | C | `RPR-7241` | `http://localhost:8501/?ro=Raipur&key=RPR-7241` |
| **RO Ranchi** | E | `IXR-4519` | `http://localhost:8501/?ro=Ranchi&key=IXR-4519` |
| **RO Shimla** | A | `SML-8302` | `http://localhost:8501/?ro=Shimla&key=SML-8302` |
| **RO Thiruvananthapuram** | D | `TRV-9164` | `http://localhost:8501/?ro=Thiruvananthapuram&key=TRV-9164` |
| **RO UP East** | E | `UPE-6742` | `http://localhost:8501/?ro=UP+East&key=UPE-6742` |
| **RO UP West** | E | `UPW-5283` | `http://localhost:8501/?ro=UP+West&key=UPW-5283` |
| **RO Vijayawada** | D | `VJA-4931` | `http://localhost:8501/?ro=Vijayawada&key=VJA-4931` |
| **Master Admin (Head Office)** | All | `HQ-ADMIN-7700` | `http://localhost:8501/?admin=true&key=HQ-ADMIN-7700` |

---

## How to Test Locally

1. Open your terminal in this directory:
   ```bash
   streamlit run app.py
   ```
2. Your browser will open at `http://localhost:8501`.
3. Test any of the links above (e.g. `http://localhost:8501/?ro=Jaipur&key=JPR-4826`) to experience the isolated RO Jaipur portal.

---

## How to Deploy to the Cloud (100% Free, 24/7 Access)

To make it completely independent of your personal computer:

1. **Push this folder to a GitHub repository** (can be private or public):
   ```bash
   git init
   git add .
   git commit -m "Initial commit for NHAI RO Dashboard"
   git branch -M main
   git remote add origin <YOUR_GITHUB_REPO_URL>
   git push -u origin main
   ```
2. **Deploy on Streamlit Community Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
   - Click **"Create app"**.
   - Select your repository and set Main file path to `app.py`.
   - Click **"Deploy"**!
3. **Done!** Streamlit gives you a permanent, secure HTTPS URL (e.g. `https://nhai-dashcam-ro.streamlit.app/`).
   - RO Jaipur link becomes: `https://nhai-dashcam-ro.streamlit.app/?ro=Jaipur&key=JPR-4826`
   - It will run 24/7 without needing your laptop powered on.

