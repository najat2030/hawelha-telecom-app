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

# ================= STYLE & THEME (نفس ستايلك القديم بالظبط) =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap'); 
.stApp { background-color: #f8f9fa; font-family: 'Tajawal', sans-serif; } 
#MainMenu { visibility: hidden; } 
footer { visibility: hidden; } 
header { visibility: hidden; } 
.login-background { position: fixed; inset: 0; background-color: #F4F6F8; z-index: -1; } 
.login-card { background: rgba(255, 255, 255, 0.97); padding: 35px 30px; border-radius: 20px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); border: 1px solid rgba(255, 255, 255, 0.4); max-width: 430px; margin: 70px auto; text-align: center; } 
.login-title { color: #1a7e43; font-size: 26px; font-weight: 800; margin-bottom: 20px; } 
.login-subtitle { color: #666; font-size: 14px; margin-bottom: 20px; } 
.royal-green-box, div.stButton > button { background-color: #1a7e43 !important; color: white !important; border-radius: 50px !important; border: 2px solid #146435 !important; font-family: 'Segoe UI', sans-serif; font-weight: 600 !important; display: flex; align-items: center; justify-content: center; transition: all 0.3s ease; margin: 0 !important; } 
.royal-green-box { min-height: 45px !important; max-height: 45px !important; width: fit-content !important; padding: 5px 16px !important; font-size: 14px !important; gap: 8px !important; white-space: nowrap !important; margin-left: auto !important; } 
div.stButton > button { min-height: 45px !important; max-height: 45px !important; width: 100% !important; font-size: 14px !important; } 
.avatar-circle-white { background-color: white !important; color: #1a7e43 !important; border-radius: 50%; width: 28px; height: 28px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0; margin-left: 8px; } 
.header-container { background: white; padding: 10px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; text-align: center; } 
.header-logo { width: 100% !important; max-width: 650px !important; height: auto; } 
.metric-card { background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-right: 5px solid #1a7e43; margin-bottom: 10px; text-align: center; } 
.metric-title { font-size: 18px !important; color: #555; font-weight: 600 !important; } 
.metric-value { font-size: 32px !important; color: #1a7e43; font-weight: 800 !important; } 
.process-btn-area + div.stButton > button { background-color: #f0f2f6 !important; color: #555 !important; border: 1px solid #d1d5db !important; min-height: 50px !important; } 
.stProgress > div > div > div > div { background-color: #daa520 !important; } 
</style>
""", unsafe_allow_html=True)

# ================= USERS DATA (نفس اللوجيك القديم) =================
def load_users():
    try:
        df_users = pd.read_excel("users.xlsx")
        required_cols = {"Username", "Password"}
        if not required_cols.issubset(df_users.columns):
            st.error("ملف users.xlsx لازم يحتوي على الأعمدة: Username و Password")
            st.stop()
        return { str(row["Username"]).strip(): str(row["Password"]).strip() for _, row in df_users.iterrows() }
    except FileNotFoundError:
        st.error("ملف users.xlsx غير موجود.")
        st.stop()
    except Exception as e:
        st.error(f"خطأ في قراءة المستخدمين: {e}")
        st.stop()

users = load_users()

# ================= SESSION STATE =================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "username" not in st.session_state: st.session_state.username = ""

# ================= LOGIN PAGE =================
def login_page():
    st.markdown('<div class="login-background"></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="login-card"><div class="login-title">🔐 تسجيل الدخول</div><div class="login-subtitle">ادخلي اسم المستخدم وكلمة المرور</div></div>', unsafe_allow_html=True)
        username = st.text_input("اسم المستخدم", placeholder="اسم المستخدم 👤", label_visibility="collapsed")
        password = st.text_input("كلمة المرور", placeholder="كلمة المرور 🔒", type="password", label_visibility="collapsed")
        if st.button("تسجيل الدخول", key="login_btn"):
            if username.strip() in users and users[username.strip()] == password.strip():
                st.session_state.logged_in = True
                st.session_state.username = username.strip()
                st.rerun()
            else: st.error("⚠️ بيانات الدخول غير صحيحة")

if not st.session_state.logged_in:
    login_page()
    st.stop()

# ================= HEADER =================
logo_url = "https://raw.githubusercontent.com/najat2030/hawelha-telecom-app/main/static/logo.png"
col_out, col_logo, col_me = st.columns([1, 4, 1], vertical_alignment="center")

with col_out:
    if st.button("🚪 خروج", key="logout_btn"):
        st.session_state.logged_in = False
        st.rerun()

with col_logo:
    st.markdown(f'<div class="header-container"><img src="{logo_url}" class="header-logo"></div>', unsafe_allow_html=True)

with col_me:
    initial = st.session_state.username[0].upper()
    st.markdown(f'<div class="royal-green-box"><span class="avatar-circle-white">{initial}</span>مرحباً، {st.session_state.username}</div>', unsafe_allow_html=True)

# ================= LOGIC (تعديل منطق اللغة والترتيب) =================
def normalize(t):
    return (t or "").replace("−", "-").replace("–", "-").replace("—", "-")

def extract_numbers(text):
    if not text: return []
    text = normalize(str(text))
    text = re.sub(r'(\d)-', r'\1 -', text) # فصل السالب الملتصق
    return [float(n) for n in re.findall(r'-?\d+(?:\.\d+)?', text)]

def parse_file(file, is_arabic):
    records = []
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages[2:]:
                for table in page.extract_tables() or []:
                    for i, row in enumerate(table):
                        if not row: continue
                        text = normalize(" ".join([str(c) for c in row if c]))
                        phone = re.search(r'(01[0125]\d{8})', text)
                        if phone:
                            p = phone.group(1)
                            vals = extract_numbers(text)
                            if i + 1 < len(table):
                                nxt = extract_numbers(" ".join([str(c) for c in table[i+1] if c]))
                                if len(nxt) > len(vals): vals = nxt
                            
                            vals = [v for v in vals if str(int(v)) != str(int(p))]
                            # العكس التلقائي للعربي فقط
                            if is_arabic: vals = vals[::-1]
                            
                            def g(idx): return vals[idx] if idx < len(vals) else 0
                            records.append({
                                "محمول": p, "رسوم شهرية": g(0), "رسوم الخدمات": g(1),
                                "مكالمات محلية": g(2), "رسائل محلية": g(3), "إنترنت محلية": g(4),
                                "مكالمات دولية": g(5), "رسائل دولية": g(6), "مكالمات تجوال": g(7),
                                "رسائل تجوال": g(8), "إنترنت تجوال": g(9), "رسوم تسويات": g(10),
                                "ضرائب": g(11), "إجمالي": g(12)
                            })
    except: pass
    return records

# ================= UI =================
files = st.file_uploader("📂 رفع ملفات PDF", type=["pdf"], accept_multiple_files=True)
mode = st.radio("إعدادات اللغة", ["Auto 🤖", "عربي 🇪🇬", "English 🇺🇸"], horizontal=True)

st.markdown('<div class="process-btn-area"></div>', unsafe_allow_html=True)
if st.button("🚀 بدء المعالجة والتحليل", key="process_btn"):
    if files:
        progress_bar = st.progress(0)
        all_data = []
        for idx, file in enumerate(files):
            # كشف اللغة للملف الحالي
            file.seek(0)
            if mode == "Auto 🤖":
                try:
                    with pdfplumber.open(file) as pdf:
                        first_page_text = pdf.pages[0].extract_text() or ""
                    is_ar = True if re.search(r'[\u0600-\u06FF]', first_page_text) else False
                except: is_ar = True
            else:
                is_ar = True if mode == "عربي 🇪🇬" else False
            
            file.seek(0)
            data = parse_file(file, is_ar)
            all_data.extend(data)
            progress_bar.progress((idx + 1) / len(files))
            gc.collect()

        if all_data:
            df = pd.DataFrame(all_data)
            st.markdown("### 📈 ملخص التحليل المالي")
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1: st.markdown(f'<div class="metric-card"><div class="metric-title">📱 الخطوط</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
            with m2: st.markdown(f'<div class="metric-card"><div class="metric-title">💰 الرسوم</div><div class="metric-value">{df["رسوم شهرية"].sum():,.1f}</div></div>', unsafe_allow_html=True)
            with m3: st.markdown(f'<div class="metric-card"><div class="metric-title">🧾 تسويات</div><div class="metric-value">{df["رسوم تسويات"].sum():,.1f}</div></div>', unsafe_allow_html=True)
            with m4: st.markdown(f'<div class="metric-card"><div class="metric-title">🏛️ ضرائب</div><div class="metric-value">{df["ضرائب"].sum():,.1f}</div></div>', unsafe_allow_html=True)
            with m5: st.markdown(f'<div class="metric-card"><div class="metric-title">💎 الإجمالي</div><div class="metric-value">{df["إجمالي"].sum():,.1f}</div></div>', unsafe_allow_html=True)
            
            st.dataframe(df, use_container_width=True)
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 تحميل تقرير Excel", data=buf.getvalue(), file_name="Report.xlsx")
        else:
            st.warning("لم يتم استخراج بيانات.")
    else:
        st.info("يرجى رفع الملفات أولاً.")
