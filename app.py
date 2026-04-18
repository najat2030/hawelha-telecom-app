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

    /* ===== 1. القواعد العامة للأزرار الملكية ===== */
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

    /* ===== 2. تنسيق مربع مرحبا (أقصى اليمين وحجم مخصص) ===== */
    .royal-green-box {
        min-height: 45px !important;
        max-height: 45px !important;
        width: fit-content !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        padding: 5px 20px !important;
        font-size: 14px !important;
        gap: 10px !important;
        white-space: nowrap !important;
        direction: rtl !important;
    }

    /* ===== 3. تنسيق زر الخروج (أقصى اليسار وحجم متناسق) ===== */
    div.stButton > button {
        min-height: 45px !important;
        max-height: 45px !important;
        width: fit-content !important;
        padding: 5px 25px !important;
        margin-left: 0 !important;
        margin-right: auto !important;
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
        margin-left: 10px;
    }

    /* ===== 4. الشعار الكبير المالي لمركزه ===== */
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
        display: block;
        margin: 0 auto;
    }

    /* ===== 5. كروت التحليل المالي (توسيط كامل) ===== */
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-right: 5px solid #1a7e43;
        margin-bottom: 10px;
        text-align: center; /* توسيط المحتوى داخل الكارت */
    }
    .metric-title { 
        font-size: 18px !important; 
        color: #555; 
        font-weight: 600 !important;
        display: block;
        width: 100%;
    }
    .metric-value { 
        font-size: 32px !important; 
        color: #1a7e43; 
        font-weight: 800 !important; 
        display: block;
        width: 100%;
        margin-top: 5px;
    }

    /* ===== 6. زر المعالجة الرمادي (لون الخلفية) ===== */
    .process-btn-area + div.stButton > button {
        background-color: #f0f2f6 !important;
        color: #555 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 50px !important;
        width: 100% !important;
        box-shadow: none !important;
        min-height: 50px !important;
    }

    .process-btn-area + div.stButton > button:hover {
        background-color: #e2e8f0 !important;
        border-color: #9ca3af !important;
    }

    .stProgress > div > div > div > div {
        background-color: #daa520 !important;
    }
</style>
""", unsafe_allow_html=True)

# ================= LOGIN STATE =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.session_state.logged_in = True 
    st.session_state.username = "noga"
    st.rerun()

# ================= TOP HEADER =================
user_initial = st.session_state.username[0].upper()
logo_url = "https://raw.githubusercontent.com/najat2030/hawelha-telecom-app/main/static/logo.png"

t_left, t_center, t_right = st.columns([1, 2, 1], vertical_alignment="center")

with t_left:
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.logged_in = False
        st.rerun()

with t_center:
    st.markdown(f'<div class="header-container"><img src="{logo_url}" class="header-logo"></div>', unsafe_allow_html=True)

with t_right:
    st.markdown(f'''
    <div class="royal-green-box">
        <div class="avatar-circle-white">{user_initial}</div>
        <span>مرحباً، {st.session_state.username}</span>
    </div>
    ''', unsafe_allow_html=True)

# ================= LOGIC FUNCTIONS (STRICTLY UNTOUCHED) =================
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

# ================= MAIN UI =================
files = st.file_uploader("📂 رفع ملفات PDF", type=["pdf"], accept_multiple_files=True)

# الـ Marker لضبط لون الزرار للرمادي
st.markdown('<div class="process-btn-area"></div>', unsafe_allow_html=True)
if st.button("🚀 بدء المعالجة والتحليل"):
    if files:
        progress_bar = st.progress(0)
        all_data = []
        for idx, file in enumerate(files):
            data = parse_ar(file)
            all_data.extend(data)
            progress_bar.progress((idx + 1) / len(files))
        
        if all_data:
            df = pd.DataFrame(all_data)
            st.markdown("### 📈 ملخص التحليل المالي")
            m1, m2, m3, m4, m5 = st.columns(5)
            
            with m1: st.markdown(f'<div class="metric-card"><div class="metric-title">📱 إجمالي الخطوط</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
            with m2: st.markdown(f'<div class="metric-card"><div class="metric-title">💰 الرسوم الشهرية</div><div class="metric-value">{df["رسوم شهرية"].sum():,.0f}</div></div>', unsafe_allow_html=True)
            with m3: st.markdown(f'<div class="metric-card"><div class="metric-title">🧾 رسوم التسويات</div><div class="metric-value">{df["رسوم تسويات"].sum():,.0f}</div></div>', unsafe_allow_html=True)
            with m4: st.markdown(f'<div class="metric-card"><div class="metric-title">🏛️ إجمالي الضرائب</div><div class="metric-value">{df["ضرائب"].sum():,.0f}</div></div>', unsafe_allow_html=True)
            with m5: st.markdown(f'<div class="metric-card"><div class="metric-title">💎 الإجمالي الكلي</div><div class="metric-value">{df["إجمالي"].sum():,.0f}</div></div>', unsafe_allow_html=True)
            
            st.markdown("---")
            st.dataframe(df, use_container_width=True)
            
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 تحميل تقرير Excel", data=excel_buffer.getvalue(), file_name="Report.xlsx")
