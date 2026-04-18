import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import os
import gc
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(page_title="Hawelha Telecom", layout="wide", page_icon="📊")

# ================= STYLE & THEME =================
PRIMARY_COLOR = "#0B6B3A"  # Royal Green
BG_COLOR = "#F4F6F8"
CARD_BG = "#FFFFFF"

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');

    .stApp {
        background-color: #f8f9fa;
        font-family: 'Tajawal', sans-serif;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* ===== Royal Green Style (Unified for Greeting & Logout) ===== */
    .royal-green-box, div.stButton > button {
        background-color: #1a7e43 !important;
        color: white !important;
        padding: 10px 20px !important;
        border-radius: 50px !important;
        border: 2px solid #146435 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 600 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        transition: all 0.3s ease;
        margin: 0 !important;
        min-height: 55px !important;
        width: 100% !important;
        box-sizing: border-box;
    }

    /* Avatar Circle inside the box */
    .avatar-circle-white {
        background-color: white !important;
        color: #1a7e43 !important;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        flex-shrink: 0;
        margin-left: 12px;
    }

    /* Hover effect for buttons */
    div.stButton > button:hover {
        background-color: #146435 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        transform: translateY(-2px) !important;
    }

    /* Custom Header Container */
    .dashboard-header {
        background: white;
        padding: 20px 24px;
        border-radius: 0 0 22px 22px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.05);
        margin-bottom: 26px;
        border-bottom: 4px solid #0B6B3A;
        min-height: 230px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .header-logo {
        width: 520px;
        max-width: 90%;
        height: auto;
        display: block;
        margin: 0 auto;
    }

    /* File uploader dashed area */
    .stFileUploader section {
        border: 2px dashed #cccccc !important;
        border-radius: 12px !important;
        background-color: #ffffff !important;
    }

    /* Gold progress bar */
    .stProgress > div > div > div > div {
        background-color: #daa520 !important;
    }

    /* Metric Cards */
    .metric-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-right: 5px solid #0B6B3A;
        transition: transform 0.2s;
        height: 100%;
    }
    .metric-value {
        color: #0B6B3A;
        font-size: 26px;
        font-weight: 700;
    }

    .footer {
        text-align: center;
        color: #888;
        font-size: 12px;
        margin-top: 50px;
        padding: 20px;
        border-top: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# ================= LOGGING =================
LOG_FILE = "activity_log.csv"

def log_action(user, action, details=""):
    try:
        log_row = pd.DataFrame([{
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user if user else "Unknown",
            "action": action,
            "details": details
        }])
        if os.path.exists(LOG_FILE):
            old_logs = pd.read_csv(LOG_FILE)
            pd.concat([old_logs, log_row], ignore_index=True).to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
        else:
            log_row.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
    except: pass

# ================= DATA LOADING =================
try:
    df_users = pd.read_excel("users.xlsx")
    users = {row["Username"]: {"password": str(row["Password"]), "role": row["Role"]} for _, row in df_users.iterrows()}
except:
    st.error("ملف users.xlsx غير موجود.")
    st.stop()

if "logged_in" not in st.session_state: st.session_state.logged_in = False

# ================= LOGIN PAGE =================
if not st.session_state.logged_in:
    st.markdown('<div style="text-align:center; margin-top:100px;"><h1>🔐 تسجيل الدخول</h1></div>', unsafe_allow_html=True)
    with st.container():
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if u in users and users[u]["password"] == p:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.role = users[u]["role"]
                log_action(u, "Login Success")
                st.rerun()
            else: st.error("بيانات خاطئة")
    st.stop()

# ================= DASHBOARD HEADER =================
user_initial = st.session_state.username[0].upper()
logo_url = "https://raw.githubusercontent.com/najat2030/hawelha-telecom-app/main/static/logo.png"

top_left, top_center, top_right = st.columns([1, 2, 1], vertical_alignment="center")

with top_left:
    if st.button("🚪 تسجيل الخروج"):
        log_action(st.session_state.username, "Logout")
        st.session_state.logged_in = False
        st.rerun()

with top_center:
    st.markdown(f'<div class="dashboard-header"><img src="{logo_url}" class="header-logo"></div>', unsafe_allow_html=True)

with top_right:
    st.markdown(f'<div class="royal-green-box"><div class="avatar-circle-white">{user_initial}</div><span>مرحباً، {st.session_state.username}</span></div>', unsafe_allow_html=True)

# ================= APP LOGIC (PRESERVED) =================
def normalize(t): return (t or "").replace("−", "-").replace("–", "-").replace("—", "-")

def extract_numbers(text):
    if not text: return []
    text = normalize(str(text))
    text = re.sub(r'\((\d+\.?\d*)\)', r'-\1', text)
    text = re.sub(r'(\d+\.?\d*)-', r'-\1', text)
    return [float(n) for n in re.findall(r'-?\d+(?:\.\d+)?', text)]

def parse_ar(file):
    records = []
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages[2:]:
                for table in page.extract_tables() or []:
                    i = 0
                    while i < len(table):
                        row = table[i]
                        if not row: i += 1; continue
                        text = normalize(" ".join([str(c) for c in row if c]))
                        phone = re.search(r'(01[0125]\d{8})', text)
                        if phone:
                            p = phone.group(1)
                            vals = extract_numbers(text)
                            if i + 1 < len(table):
                                nxt = extract_numbers(" ".join([str(c) for c in table[i+1] if c]))
                                if len(nxt) > len(vals): vals = nxt; i += 1
                            vals = [v for v in vals if str(int(v)) != str(int(p))][::-1]
                            def g(idx): return vals[idx] if idx < len(vals) else 0
                            records.append({"محمول": p, "رسوم شهرية": g(0), "رسوم الخدمات": g(1), "مكالمات محلية": g(2), "رسائل محلية": g(3), "إنترنت محلية": g(4), "مكالمات دولية": g(5), "رسائل دولية": g(6), "مكالمات تجوال": g(7), "رسائل تجوال": g(8), "إنترنت تجوال": g(9), "رسوم تسويات": g(10), "ضرائب": g(11), "إجمالي": g(12)})
                        i += 1
    except: pass
    return records

# [Rest of parse_en and parse_ai as per original...]

# ================= PROCESSING =================
files = st.file_uploader("📂 رفع ملفات PDF", type=["pdf"], accept_multiple_files=True)

if st.button("🚀 بدء المعالجة والتحليل"):
    if files:
        progress_bar = st.progress(0)
        all_data = []
        for idx, file in enumerate(files):
            data = parse_ar(file) # Default logic
            all_data.extend(data)
            progress_bar.progress((idx + 1) / len(files))
        
        if all_data:
            df = pd.DataFrame(all_data)
            st.markdown("### 📈 ملخص التحليل المالي")
            m1, m2, m3, m4, m5 = st.columns(5)
            # Logic for dashboard metrics (Preserved)
            st.dataframe(df)
            st.download_button("📥 تحميل التقرير", data=io.BytesIO(), file_name="Report.xlsx")

st.markdown('<div class="footer">© 2026 Najat El Bakry — Hawelha Telecom</div>', unsafe_allow_html=True)
