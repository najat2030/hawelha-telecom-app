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

    /* ===== شاشة تسجيل الدخول ===== */
    .login-background {
        position: fixed;
        inset: 0;
        background-color: #F4F6F8;
        z-index: -1;
    }
    .login-card {
        background: rgba(255, 255, 255, 0.97);
        padding: 35px 30px;
        border-radius: 20px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.08);
        border: 1px solid rgba(255, 255, 255, 0.4);
        max-width: 430px;
        margin: 70px auto;
        text-align: center;
    }
    .login-title { color: #1a7e43; font-size: 26px; font-weight: 800; margin-bottom: 20px; }

    /* ===== الأزرار الملكية ===== */
    .royal-green-box, div.stButton > button {
        background-color: #1a7e43 !important;
        color: white !important;
        border-radius: 50px !important;
        border: 2px solid #146435 !important;
        font-family: 'Tajawal', sans-serif;
        font-weight: 600 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
    }

    /* مربع مرحبا */
    .royal-green-box {
        min-height: 45px !important;
        max-height: 45px !important;
        width: fit-content !important;
        padding: 5px 16px !important;
        font-size: 14px !important;
        gap: 8px !important;
        white-space: nowrap !important;
        margin-left: auto !important;
    }

    /* زر تسجيل الخروج لضمان الاستجابة */
    div.stButton > button {
        min-height: 45px !important;
        max-height: 45px !important;
        width: 100% !important;
        font-size: 14px !important;
        cursor: pointer !important;
    }

    .avatar-circle-white {
        background-color: white !important;
        color: #1a7e43 !important;
        border-radius: 50%;
        width: 28px;
        height: 28px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        flex-shrink: 0;
        margin-left: 8px;
    }

    /* الشعار */
    .header-container {
        background: white;
        padding: 10px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        text-align: center;
    }
    .header-logo { width: 100% !important; max-width: 650px !important; height: auto; }

    /* الكروت مع التوسيط الكامل */
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-right: 5px solid #1a7e43;
        margin-bottom: 10px;
        text-align: center;
    }
    .metric-title { font-size: 18px !important; color: #555; font-weight: 600 !important; }
    .metric-value { font-size: 32px !important; color: #1a7e43; font-weight: 800 !important; }

    /* زر المعالجة الرمادي */
    .process-btn-area + div.stButton > button {
        background-color: #f0f2f6 !important;
        color: #555 !important;
        border: 1px solid #d1d5db !important;
        min-height: 50px !important;
        width: 100% !important;
        box-shadow: none !important;
    }

    .stProgress > div > div > div > div { background-color: #daa520 !important; }
</style>
""", unsafe_allow_html=True)

# ================= USERS DATA =================
def load_users():
    try:
        # تأكدي أن اسم الملف يطابق الموجود عندك بالضبط
        df_users = pd.read_excel("users.xlsx")
        return {str(row["Username"]).strip(): str(row["Password"]).strip() for _, row in df_users.iterrows()}
    except:
        # يوزرات افتراضية في حالة فشل الملف عشان التطبيق ما يقفش
        return {"noga": "123", "admin": "admin"}

users = load_users()

# ================= LOGIN CHECK =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="login-background"></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="login-card"><div class="login-title">🔐 تسجيل الدخول</div></div>', unsafe_allow_html=True)
        user_input = st.text_input("Username", placeholder="اسم المستخدم 👤", label_visibility="collapsed")
        pass_input = st.text_input("Password", placeholder="كلمة المرور 🔒", type="password", label_visibility="collapsed")
        if st.button("دخول", use_container_width=True):
            if user_input in users and users[user_input] == pass_input:
                st.session_state.logged_in = True
                st.session_state.username = user_input
                st.rerun()
            else:
                st.error("بيانات غير صحيحة")
    st.stop()

# ================= HEADER =================
logo_url = "https://raw.githubusercontent.com/najat2030/hawelha-telecom-app/main/static/logo.png"
col_out, col_logo, col_me = st.columns([1, 4, 1], vertical_alignment="center")

with col_out:
    if st.button("🚪 خروج", key="logout_main"):
        st.session_state.logged_in = False
        st.rerun()

with col_logo:
    st.markdown(f'<div class="header-container"><img src="{logo_url}" class="header-logo"></div>', unsafe_allow_html=True)

with col_me:
    user_initial = st.session_state.username[0].upper()
    st.markdown(f'''
    <div class="royal-green-box">
        <div class="avatar-circle-white">{user_initial}</div>
        <span>مرحباً، {st.session_state.username}</span>
    </div>
    ''', unsafe_allow_html=True)

# ================= LOGIC =================
def normalize(t): return (t or "").replace("−", "-").replace("–", "-").replace("—", "-")
def extract_numbers(text):
    text = normalize(str(text))
    text = re.sub(r'\((\d+\.?\d*)\)', r'-\1', text)
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
                            records.append({"محمول": p, "رسوم شهرية": g(0), "رسوم تسويات": g(10), "ضرائب": g(11), "إجمالي": g(12)})
                        i += 1
    except: pass
    return records

# ================= UI =================
files = st.file_uploader("📂 رفع ملفات PDF", type=["pdf"], accept_multiple_files=True)
st.markdown('<div class="process-btn-area"></div>', unsafe_allow_html=True)

if st.button("🚀 بدء المعالجة والتحليل", key="proc_btn"):
    if files:
        prog = st.progress(0)
        all_data = []
        for idx, f in enumerate(files):
            all_data.extend(parse_ar(f))
            prog.progress((idx + 1) / len(files))
        
        if all_data:
            df = pd.DataFrame(all_data)
            st.markdown("### 📈 ملخص التحليل المالي")
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1: st.markdown(f'<div class="metric-card"><div class="metric-title">📱 الخطوط</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
            with m2: st.markdown(f'<div class="metric-card"><div class="metric-title">💰 الرسوم</div><div class="metric-value">{df["رسوم شهرية"].sum():,.0f}</div></div>', unsafe_allow_html=True)
            with m3: st.markdown(f'<div class="metric-card"><div class="metric-title">🧾 التسويات</div><div class="metric-value">{df["رسوم تسويات"].sum():,.0f}</div></div>', unsafe_allow_html=True)
            with m4: st.markdown(f'<div class="metric-card"><div class="metric-title">🏛️ الضرائب</div><div class="metric-value">{df["ضرائب"].sum():,.0f}</div></div>', unsafe_allow_html=True)
            with m5: st.markdown(f'<div class="metric-card"><div class="metric-title">💎 الإجمالي</div><div class="metric-value">{df["إجمالي"].sum():,.0f}</div></div>', unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True)
