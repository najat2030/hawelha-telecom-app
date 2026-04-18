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
        margin: 70px auto 20px auto;
        text-align: center;
    }

    .login-title {
        color: #1a7e43;
        font-size: 26px;
        font-weight: 800;
        margin-bottom: 20px;
    }

    .login-subtitle {
        color: #666;
        font-size: 14px;
        margin-bottom: 20px;
    }

    /* ===== الأزرار الملكية الأساسية ===== */
    .royal-green-box, div.stButton > button {
        background-color: #1a7e43 !important;
        color: white !important;
        border-radius: 50px !important;
        border: 2px solid #146435 !important;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        margin: 0 !important;
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

    /* زر تسجيل الخروج */
    div.stButton > button {
        min-height: 45px !important;
        max-height: 45px !important;
        width: 100% !important;
        font-size: 14px !important;
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

    .header-logo {
        width: 100% !important;
        max-width: 650px !important;
        height: auto;
    }

    /* الكروت والتحليل */
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-right: 5px solid #1a7e43;
        margin-bottom: 10px;
        text-align: center;
    }

    .metric-title {
        font-size: 18px !important;
        color: #555;
        font-weight: 600 !important;
    }

    .metric-value {
        font-size: 32px !important;
        color: #1a7e43;
        font-weight: 800 !important;
    }

    /* زر المعالجة الرمادي */
    .process-btn-area + div.stButton > button {
        background-color: #f0f2f6 !important;
        color: #555 !important;
        border: 1px solid #d1d5db !important;
        min-height: 50px !important;
    }

    /* Progress Bar Gold */
    .stProgress > div > div > div > div {
        background-color: #daa520 !important;
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

# ================= USERS DATA =================
def load_users():
    try:
        df_users = pd.read_excel("users.xlsx")
        required_cols = {"Username", "Password"}
        if not required_cols.issubset(df_users.columns):
            st.error("ملف users.xlsx لازم يحتوي على الأعمدة: Username و Password")
            st.stop()

        return {
            str(row["Username"]).strip(): str(row["Password"]).strip()
            for _, row in df_users.iterrows()
        }
    except FileNotFoundError:
        st.error("ملف users.xlsx غير موجود. ارفعيه في نفس مجلد التطبيق.")
        st.stop()
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة users.xlsx: {e}")
        st.stop()

users = load_users()

# ================= SESSION STATE =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# ================= LOGIN PAGE =================
def login_page():
    st.markdown('<div class="login-background"></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown("""
        <div class="login-card">
            <div class="login-title">🔐 تسجيل الدخول</div>
            <div class="login-subtitle">ادخلي اسم المستخدم وكلمة المرور للمتابعة</div>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input(
            "اسم المستخدم",
            placeholder="اسم المستخدم 👤",
            label_visibility="collapsed"
        )
        password = st.text_input(
            "كلمة المرور",
            placeholder="كلمة المرور 🔒",
            type="password",
            label_visibility="collapsed"
        )

        if st.button("تسجيل الدخول", key="login_btn", use_container_width=True):
            username = username.strip()
            password = password.strip()

            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("⚠️ اسم المستخدم أو كلمة المرور غير صحيحة")

# ================= LOGIN CHECK =================
if not st.session_state.logged_in:
    login_page()
    st.stop()

# ================= HEADER =================
logo_url = "https://raw.githubusercontent.com/najat2030/hawelha-telecom-app/main/static/logo.png"

col_out, col_logo, col_me = st.columns([1, 4, 1], vertical_alignment="center")

with col_out:
    if st.button("🚪 تسجيل الخروج", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

with col_logo:
    st.markdown(
        f'<div class="header-container"><img src="{logo_url}" class="header-logo"></div>',
        unsafe_allow_html=True
    )

with col_me:
    user_initial = st.session_state.username[0].upper() if st.session_state.username else "?"
    st.markdown(f'''
    <div class="royal-green-box" style="margin-left: auto;">
        <div class="avatar-circle-white">{user_initial}</div>
        <span>مرحباً، {st.session_state.username}</span>
    </div>
    ''', unsafe_allow_html=True)

# ================= MODE SELECTION =================
mode = st.radio(
    "🌐 وضع التحليل",
    ["Auto 🤖", "عربي 🇪", "English 🌍"],
    horizontal=True,
    label_visibility="collapsed"
)

# ================= LOGIC =================
def normalize(t):
    return (t or "").replace("−", "-").replace("–", "-").replace("—", "-")

def extract_numbers(text):
    if not text:
        return []
    text = normalize(str(text))
    text = re.sub(r'\((\d+\.?\d*)\)', r'-\1', text)
    text = re.sub(r'(\d+\.?\d*)-', r'-\1', text)
    text = re.sub(r'-\s+(\d)', r'-\1', text)
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
                        if not row:
                            i += 1
                            continue

                        text = normalize(" ".join([str(c) for c in row if c]))
                        phone = re.search(r'(01[0125]\d{8})', text)

                        if phone:
                            p = phone.group(1)
                            vals = extract_numbers(text)

                            if i + 1 < len(table):
                                nxt = extract_numbers(" ".join([str(c) for c in table[i+1] if c]))
                                if len(nxt) > len(vals):
                                    vals = nxt
                                    i += 1

                            vals = [v for v in vals if str(int(v)) != str(int(p))][::-1]

                            def g(idx):
                                return vals[idx] if idx < len(vals) else 0

                            records.append({
                                "محمول": p,
                                "رسوم شهرية": g(0),
                                "رسوم الخدمات": g(1),
                                "مكالمات محلية": g(2),
                                "رسائل محلية": g(3),
                                "إنترنت محلية": g(4),
                                "مكالمات دولية": g(5),
                                "رسائل دولية": g(6),
                                "مكالمات تجوال": g(7),
                                "رسائل تجوال": g(8),
                                "إنترنت تجوال": g(9),
                                "رسوم تسويات": g(10),
                                "ضرائب": g(11),
                                "إجمالي": g(12)
                            })
                        i += 1
    except Exception:
        pass
    return records

def parse_en(file):
    records = []
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages[2:]:
                for table in page.extract_tables() or []:
                    i = 0
                    while i < len(table):
                        row = table[i]
                        if not row:
                            i += 1
                            continue

                        text = " ".join([str(c) for c in row if c])
                        phone = re.search(r'(01[0125]\d{8})', text)

                        if phone:
                            p = phone.group(1)

                            next_text = ""
                            if i + 1 < len(table):
                                next_text = " ".join([str(c) for c in table[i + 1] if c])

                            vals = extract_numbers(next_text)
                            vals = [v for v in vals if str(int(v)) != str(int(p))]

                            records.append({
                                "محمول": p,
                                "رسوم شهرية": vals[0] if len(vals) > 0 else 0,
                                "رسوم الخدمات": vals[1] if len(vals) > 1 else 0,
                                "مكالمات محلية": vals[2] if len(vals) > 2 else 0,
                                "رسائل محلية": vals[3] if len(vals) > 3 else 0,
                                "إنترنت محلية": vals[4] if len(vals) > 4 else 0,
                                "مكالمات دولية": vals[5] if len(vals) > 5 else 0,
                                "رسائل دولية": vals[6] if len(vals) > 6 else 0,
                                "مكالمات تجوال": vals[7] if len(vals) > 7 else 0,
                                "رسائل تجوال": vals[8] if len(vals) > 8 else 0,
                                "إنترنت تجوال": vals[9] if len(vals) > 9 else 0,
                                "رسوم تسويات": vals[10] if len(vals) > 10 else 0,
                                "ضرائب": vals[11] if len(vals) > 11 else 0,
                                "إجمالي": vals[-1] if vals else 0
                            })

                            i += 2
                            continue

                        i += 1
    except Exception:
        pass
    return records

# ================= UI =================
files = st.file_uploader("📂 رفع ملفات PDF", type=["pdf"], accept_multiple_files=True)

st.markdown('<div class="process-btn-area"></div>', unsafe_allow_html=True)
if st.button("🚀 بدء المعالجة والتحليل", key="process_btn"):
    if files:
        progress_bar = st.progress(0)
        all_data = []

        for idx, file in enumerate(files):
            if mode == "English 🌍":
                data = parse_en(file)
            elif mode == "عربي 🇪":
                data = parse_ar(file)
            else:
                data = parse_ar(file)
                if not data:
                    file.seek(0)
                    data = parse_en(file)

            all_data.extend(data)
            progress_bar.progress((idx + 1) / len(files))
            gc.collect()

        if all_data:
            df = pd.DataFrame(all_data)

            st.markdown("### 📈 ملخص التحليل المالي")
            m1, m2, m3, m4, m5 = st.columns(5)

            with m1:
                st.markdown(f'<div class="metric-card"><div class="metric-title">📱 إجمالي الخطوط</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="metric-card"><div class="metric-title">💰 الرسوم الشهرية</div><div class="metric-value">{df["رسوم شهرية"].sum():,.0f}</div></div>', unsafe_allow_html=True)
            with m3:
                st.markdown(f'<div class="metric-card"><div class="metric-title">🧾 رسوم التسويات</div><div class="metric-value">{df["رسوم تسويات"].sum():,.0f}</div></div>', unsafe_allow_html=True)
            with m4:
                st.markdown(f'<div class="metric-card"><div class="metric-title">🏛️ إجمالي الضرائب</div><div class="metric-value">{df["ضرائب"].sum():,.0f}</div></div>', unsafe_allow_html=True)
            with m5:
                st.markdown(f'<div class="metric-card"><div class="metric-title">💎 الإجمالي الكلي</div><div class="metric-value">{df["إجمالي"].sum():,.0f}</div></div>', unsafe_allow_html=True)

            st.markdown("---")
            st.dataframe(df, use_container_width=True)

            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)

            st.download_button(
                "📥 تحميل تقرير Excel",
                data=excel_buffer.getvalue(),
                file_name="Report.xlsx"
            )
        else:
            st.warning("لم يتم استخراج بيانات من الملفات.")
    else:
        st.info("يرجى رفع الملفات أولاً.")

# ================= FOOTER =================
st.markdown("""
<div class="footer">
    © 2026 Najat El Bakry — All Rights Reserved | Powered by Streamlit
</div>
""", unsafe_allow_html=True)
