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
.stApp { background-color: #f8f9fa; font-family: 'Tajawal', sans-serif; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
.login-background { position: fixed; inset: 0; background-color: #F4F6F8; z-index: -1; }
.login-card { background: rgba(255, 255, 255, 0.97); padding: 35px 30px; border-radius: 20px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); border: 1px solid rgba(255, 255, 255, 0.4); max-width: 430px; margin: 70px auto; text-align: center; }
.login-title { color: #1a7e43; font-size: 26px; font-weight: 800; margin-bottom: 20px; }
.royal-green-box, div.stButton > button { background-color: #1a7e43 !important; color: white !important; border-radius: 50px !important; border: 2px solid #146435 !important; font-family: 'Segoe UI', sans-serif; font-weight: 600 !important; display: flex; align-items: center; justify-content: center; transition: all 0.3s ease; margin: 0 !important; }
.royal-green-box { min-height: 45px !important; width: fit-content !important; padding: 5px 16px !important; font-size: 14px !important; gap: 8px !important; margin-left: auto !important; }
div.stButton > button { min-height: 45px !important; width: 100% !important; font-size: 14px !important; }
.avatar-circle-white { background-color: white !important; color: #1a7e43 !important; border-radius: 50%; width: 28px; height: 28px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin-left: 8px; }
.header-container { background: white; padding: 10px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; text-align: center; }
.header-logo { width: 100% !important; max-width: 650px !important; height: auto; }
.metric-card { background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-right: 5px solid #1a7e43; margin-bottom: 10px; text-align: center; }
.metric-title { font-size: 18px !important; color: #555; font-weight: 600 !important; }
.metric-value { font-size: 32px !important; color: #1a7e43; font-weight: 800 !important; }
.stProgress > div > div > div > div { background-color: #daa520 !important; }
</style>
""", unsafe_allow_html=True)

# ================= USERS DATA =================
def load_users():
    try:
        df_users = pd.read_excel("users.xlsx")
        return {
            str(row["Username"]).strip(): str(row["Password"]).strip()
            for _, row in df_users.iterrows()
        }
    except:
        return {"admin": "123"}

users = load_users()

# ================= SESSION STATE =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(
            '<div class="login-card"><div class="login-title">🔐 تسجيل الدخول</div></div>',
            unsafe_allow_html=True
        )
        u = st.text_input("Username", placeholder="اسم المستخدم", label_visibility="collapsed")
        p = st.text_input("Password", placeholder="كلمة المرور", type="password", label_visibility="collapsed")
        if st.button("دخول"):
            if u.strip() in users and users[u.strip()] == p.strip():
                st.session_state.logged_in = True
                st.session_state.username = u.strip()
                st.rerun()
            else:
                st.error("خطأ في البيانات")
    st.stop()

# ================= HEADER =================
logo_url = "https://raw.githubusercontent.com/najat2030/hawelha-telecom-app/main/static/logo.png"
col_out, col_logo, col_me = st.columns([1, 4, 1], vertical_alignment="center")

with col_out:
    if st.button("🚪 خروج"):
        st.session_state.logged_in = False
        st.rerun()

with col_logo:
    st.markdown(
        f'<div class="header-container"><img src="{logo_url}" class="header-logo"></div>',
        unsafe_allow_html=True
    )

with col_me:
    initial = st.session_state.username[0].upper()
    st.markdown(
        f'<div class="royal-green-box"><span class="avatar-circle-white">{initial}</span>مرحباً، {st.session_state.username}</div>',
        unsafe_allow_html=True
    )

# ================= HELPERS =================
def normalize(t):
    return (t or "").replace("−", "-").replace("–", "-").replace("—", "-")

def extract_numbers(text):
    """
    نسخة مدموجة من معالجة السالب في النصّة الأولى
    مع الحفاظ على استخلاص أرقام نظيف.
    """
    if not text:
        return []

    text = normalize(str(text))

    # لو الرقم مكتوب بين أقواس اعتبره سالب
    text = re.sub(r'\((\d+\.?\d*)\)', r'-\1', text)

    # بعض الـ PDFs بتلخبط الشرطة بعد الرقم أو قبله
    text = re.sub(r'(\d+\.?\d*)-', r'-\1', text)
    text = re.sub(r'-\s+(\d)', r'-\1', text)

    numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
    return [float(n) for n in numbers]

def detect_language(file):
    """
    الكشف التلقائي للغة من أول صفحة
    """
    try:
        file.seek(0)
        with pdfplumber.open(file) as pdf:
            text = pdf.pages[0].extract_text() or ""
        return "ar" if re.search(r'[\u0600-\u06FF]', text) else "en"
    except:
        return "ar"

def parse_file(file, lang):
    records = []

    try:
        file.seek(0)
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages[2:]:
                tables = page.extract_tables() or []

                for table in tables:
                    i = 0
                    while i < len(table):
                        row = table[i]

                        if not row:
                            i += 1
                            continue

                        text = normalize(" ".join([str(c) for c in row if c]))
                        phone_match = re.search(r'(01[0125]\d{8})', text)

                        if not phone_match:
                            i += 1
                            continue

                        phone = phone_match.group(1)

                        # نقرأ أرقام الصف الحالي
                        vals = extract_numbers(text)

                        # لو الصف اللي بعده فيه تفاصيل أكثر، ناخده
                        if i + 1 < len(table):
                            next_text = " ".join([str(c) for c in table[i + 1] if c])
                            nxt = extract_numbers(next_text)
                            if len(nxt) > len(vals):
                                vals = nxt
                                if lang == "ar":
                                    i += 1

                        # نشيل رقم الموبايل لو دخل بالغلط ضمن القيم
                        cleaned_vals = []
                        for v in vals:
                            try:
                                if str(int(v)) == phone:
                                    continue
                            except:
                                pass
                            cleaned_vals.append(v)
                        vals = cleaned_vals

                        # العربي غالبًا بيكون معكوس
                        if lang == "ar":
                            vals = vals[::-1]

                        def g(idx):
                            return vals[idx] if idx < len(vals) else 0

                        taswiya = g(10)
                        if taswiya > 0:
                            taswiya = taswiya * -1

                        records.append({
                            "محمول": phone,
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
                            "رسوم تسويات": taswiya,
                            "ضرائب": g(11),
                            "إجمالي": g(12)
                        })

                        if lang == "en":
                            i += 2
                        else:
                            i += 1

    except:
        pass

    return records

# ================= UI =================
files = st.file_uploader("📂 رفع ملفات PDF", type=["pdf"], accept_multiple_files=True)
mode = st.radio("إعدادات اللغة", ["Auto 🤖", "عربي 🇪🇬", "English 🇺🇸"], horizontal=True)

if st.button("🚀 بدء المعالجة والتحليل"):
    if files:
        progress_bar = st.progress(0)
        status_text = st.empty()

        all_data = []
        failed_files = []

        total_files = len(files)

        for idx, file in enumerate(files):
            try:
                status_text.text(f"📄 جاري معالجة: {file.name}")

                if mode == "Auto 🤖":
                    lang = detect_language(file)
                else:
                    lang = "ar" if mode == "عربي 🇪🇬" else "en"

                file.seek(0)
                data = parse_file(file, lang)

                if data:
                    all_data.extend(data)
                else:
                    failed_files.append(file.name)

            except:
                failed_files.append(file.name)

            progress_bar.progress((idx + 1) / total_files)
            gc.collect()

        status_text.text("✅ اكتملت المعالجة")

        if all_data:
            df = pd.DataFrame(all_data)

            st.markdown("### 📈 ملخص التحليل المالي")
            m1, m2, m3, m4, m5 = st.columns(5)

            with m1:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-title">📱 الخطوط</div><div class="metric-value">{len(df)}</div></div>',
                    unsafe_allow_html=True
                )
            with m2:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-title">💰 الرسوم</div><div class="metric-value">{df["رسوم شهرية"].sum():,.1f}</div></div>',
                    unsafe_allow_html=True
                )
            with m3:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-title">🧾 تسويات</div><div class="metric-value" style="color: red;">{df["رسوم تسويات"].sum():,.1f}</div></div>',
                    unsafe_allow_html=True
                )
            with m4:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-title">🏛️ ضرائب</div><div class="metric-value">{df["ضرائب"].sum():,.1f}</div></div>',
                    unsafe_allow_html=True
                )
            with m5:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-title">💎 الإجمالي</div><div class="metric-value">{df["إجمالي"].sum():,.1f}</div></div>',
                    unsafe_allow_html=True
                )

            st.dataframe(df, use_container_width=True)

            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)

            st.download_button(
                "📥 تحميل تقرير Excel",
                data=buf.getvalue(),
                file_name="Telecom_Report.xlsx"
            )

            if failed_files:
                st.warning(f"⚠️ ملفات فشل استخراجها: {len(failed_files)}")
                st.write(failed_files)

        else:
            st.error("لم يتم استخراج أي بيانات من الملفات")

# ================= SIGNATURE =================
st.markdown("""
<div style="text-align:center; margin-top:40px; font-weight:bold;">
Developed by Najat El Bakry © 2026
</div>
""", unsafe_allow_html=True)
