import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
import gc

# ================= CONFIG =================
st.set_page_config(page_title="Hawelha Telecom", layout="wide", page_icon="📊")

# ================= STYLE & THEME =================
PRIMARY_COLOR = "#0B6B3A"
BG_COLOR = "#F4F6F8"
CARD_BG = "#FFFFFF"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');

    .stApp {{
        background-color: {BG_COLOR};
        font-family: 'Tajawal', sans-serif;
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    .login-background {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: url('/static/logo.png'); 
        background-size: contain;
        background-position: center;
        background-repeat: no-repeat;
        z-index: -1;
        opacity: 1;
    }}

    .login-card {{
        background: rgba(255, 255, 255, 0.95);
        padding: 40px;
        border-radius: 20px;
        max-width: 400px;
        margin: 80px auto;
        text-align: center;
    }}

    .dashboard-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: white;
        padding: 15px 30px;
        border-radius: 0 0 20px 20px;
        margin-bottom: 30px;
        border-bottom: 4px solid {PRIMARY_COLOR};
    }}

    .metric-card {{
        background: white;
        padding: 25px;
        border-radius: 15px;
        border-right: 5px solid {PRIMARY_COLOR};
    }}

    .metric-title {{
        color: #666;
        font-size: 15px;
    }}

    .metric-value {{
        color: {PRIMARY_COLOR};
        font-size: 26px;
        font-weight: bold;
    }}

</style>
""", unsafe_allow_html=True)

# ================= USERS =================
df_users = pd.read_excel("users.xlsx")
users = {
    row["Username"]: {
        "password": str(row["Password"]),
        "role": row["Role"]
    }
    for _, row in df_users.iterrows()
}

# ================= SESSION =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ================= LOGIN =================
def login_page():
    st.markdown('<div class="login-background"></div>', unsafe_allow_html=True)
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور", type="password")

    if st.button("تسجيل الدخول"):
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]
            st.rerun()

# ================= MAIN =================
if not st.session_state.logged_in:
    login_page()
    st.stop()

# ================= HEADER =================
col1, col2 = st.columns([6,2])

with col1:
    st.markdown("## 📊 Dashboard")

with col2:
    st.write(f"👤 {st.session_state.username}")

    if st.session_state.role == "admin":
        if st.button("⚙️ Manage app"):
            st.session_state.show_admin = True

    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()

# ================= MODE =================
mode = st.radio("", ["Auto 🤖","عربي 🇪","English 🌍"], horizontal=True)

# ================= HELPERS =================
def normalize(t):
    return (t or "").replace("−","-")

def extract_numbers(text):
    if not text:
        return []
    return [float(n) for n in re.findall(r'-?\d+(?:\.\d+)?', text)]

def clean_numbers(vals, phone):
    return vals

def fix_phone(phone):
    return phone

# ================= PARSERS =================
def parse_ar(file): return []
def parse_en(file): return []
def parse_ai(file): return []

# ================= EXCEL =================
def to_excel(df):
    out = io.BytesIO()
    df.to_excel(out,index=False)
    return out

# ================= PROCESS =================
files = st.file_uploader("📂 رفع ملفات PDF", type=["pdf"], accept_multiple_files=True)

if files:
    if st.button("🚀 بدء المعالجة"):
        
        progress = st.progress(0)
        all_data = []

        for i, file in enumerate(files):
            progress.progress((i+1)/len(files))

            if mode == "English 🌍":
                data = parse_en(file)

            elif mode == "Auto 🤖":
                data = parse_ar(file)
                if not data:
                    data = parse_en(file)
                if not data:
                    data = parse_ai(file)

            else:
                data = parse_ar(file)

            if not data:
                data = parse_ai(file)

            all_data.extend(data)

        if all_data:
            df = pd.DataFrame(all_data)

            st.write("### 📊 النتائج")

            st.write("عدد الخطوط:", len(df))

            st.download_button(
                "تحميل Excel",
                to_excel(df),
                "report.xlsx"
            )
