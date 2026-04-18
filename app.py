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

st.markdown(f"""<style>...</style>""", unsafe_allow_html=True)

# ================= USERS DATA LOADING =================
try:
    df_users = pd.read_excel("users.xlsx")
    users = {
        row["Username"]: {
            "password": str(row["Password"]),
            "role": row["Role"]
        }
        for _, row in df_users.iterrows()
    }
except FileNotFoundError:
    st.error("ملف users.xlsx غير موجود.")
    st.stop()

# ================= SESSION =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "show_admin_panel" not in st.session_state:
    st.session_state.show_admin_panel = False

# ================= LOGIN =================
def login_page():
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور", type="password")

    if st.button("تسجيل الدخول"):
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]
            st.rerun()
        else:
            st.error("بيانات غلط")

if not st.session_state.logged_in:
    login_page()
    st.stop()

# ================= MODE =================
mode = st.radio(
    "mode",
    ["Auto 🤖", "عربي 🇪", "English 🌍"]
)

# =========================================================
# 🚫 DO NOT MODIFY BELOW THIS LINE 🚫
# =========================================================

def normalize(t):
    return (t or "").replace("−","-").replace("–","-").replace("—","-")

def extract_numbers(text):
    if not text:
        return []
    text = normalize(str(text))
    text = re.sub(r'\((\d+\.?\d*)\)', r'-\1', text)
    text = re.sub(r'(\d+\.?\d*)-', r'-\1', text)
    text = re.sub(r'-\s+(\d)', r'-\1', text)
    numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
    return [float(n) for n in numbers]

def clean_numbers(vals, phone):
    phone_int = str(int(phone))
    return [v for v in vals if str(int(v)) != phone_int]

def fix_phone(phone):
    phone = str(phone)
    if len(phone) == 10 and phone.startswith("1"):
        return "0" + phone
    return phone

# ================= PARSERS =================
def parse_ar(file):
    return []

def parse_en(file):
    return []

def parse_ai(file):
    return []

# ================= EXCEL =================
def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    out.seek(0)
    return out

# ================= MAIN =================
files = st.file_uploader("PDF", type=["pdf"], accept_multiple_files=True)

if files:
    if st.button("Start"):
        
        all_data = []

        for file in files:

            # ✅ FIXED
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

            # ✅ FIXED
            if not data:
                data = parse_ai(file)

            all_data.extend(data)

        # ✅ FIXED
        if all_data:
            df_result = pd.DataFrame(all_data)

            st.dataframe(df_result)

            st.download_button(
                "Download",
                data=to_excel(df_result),
                file_name="report.xlsx"
            )
