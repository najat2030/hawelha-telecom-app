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

    /* ===== Royal Green Header Boxes (Unified & Symmetrical) ===== */
    .royal-green-box, div.stButton > button {
        background-color: #1a7e43 !important;
        color: white !important;
        padding: 5px 10px !important;
        border-radius: 50px !important;
        border: 2px solid #146435 !important;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        transition: all 0.3s ease;
        margin: 0 !important;
        min-height: 45px !important;
        max-height: 45px !important;
        width: 100% !important;
        box-sizing: border-box;
        font-size: 14px !important;
    }

    /* ===== تعديل مربع مرحباً فقط ليبقى نفس حجم الزر ===== */
    .royal-green-box {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 100% !important;
        padding: 5px 12px !important;
        gap: 8px !important;
        overflow: hidden;
        white-space: nowrap;
    }

    /* Avatar Circle inside the box */
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

    /* Hover effect */
    div.stButton > button:hover {
        background-color: #146435 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        transform: translateY(-1px) !important;
    }

    /* Dashboard Header Logo Area */
    .header-container {
        background: white;
        padding: 10px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        text-align: center;
    }

    .header-logo {
        width: 400px;
        max-width: 80%;
        height: auto;
    }

    /* Metric Cards (Dashboard) */
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-right: 5px solid #1a7e43;
        margin-bottom: 10px;
    }
    .metric-title { font-size: 14px; color: #666; font-weight: 500; }
    .metric-value { font-size: 22px; color: #1a7e43; font-weight: 700; }

    /* Progress Bar Gold */
    .stProgress > div > div > div > div {
        background-color: #daa520 !important;
    }
</style>
""", unsafe_allow_html=True)

# ================= LOGIN LOGIC (PRESERVED) =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # (كود تسجيل الدخول الخاص بك يوضع هنا - تم اختصاره للعرض)
    st.session_state.logged_in = True 
    st.session_state.username = "noga"
    st.rerun()

# ================= TOP HEADER (SYMMETRICAL) =================
user_initial = st.session_state.username[0].upper()
logo_url = "https://raw.githubusercontent.com/najat2030/hawelha-telecom-app/main/static/logo.png"

t_left, t_center, t_right = st.columns([1, 2, 1], vertical_alignment="center")

with t_left:
    # زر الخروج مع أيقونة بيضاء (باستخدام اللون الأبيض في النص)
    if st.button(" تسجيل الخروج"):
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

# ================= UPLOAD & PROCESS =================
files = st.file_uploader("📂 رفع ملفات PDF", type=["pdf"], accept_multiple_files=True)

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
            
            # --- DASHBOARD (RETURNED TO POSITION) ---
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
        else:
            st.warning("لم يتم استخراج بيانات من الملفات.")
    else:
        st.info("يرجى رفع الملفات أولاً.")
