import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
import gc

# ================= CONFIG & STYLE =================
st.set_page_config(
    page_title="Hawelha Telecom | حوّلها تليكوم",
    page_icon="📊",
    layout="wide"
)

# تصميم الـ CSS للألوان الخضراء الملوكي والأبيض
st.markdown("""
    <style>
    /* تغيير الخلفية العامة */
    .stApp {
        background-color: #ffffff;
    }
    
    /* ستايل القائمة الجانبية */
    [data-testid="stSidebar"] {
        background-color: #004d40;
        color: white;
    }

    /* ستايل العناوين والكروت */
    .main-title {
        color: #004d40;
        text-align: center;
        font-family: 'Cairo', sans-serif;
        font-weight: bold;
        padding: 20px;
    }
    
    .metric-card {
        background-color: #f1f8e9;
        border-left: 5px solid #004d40;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }

    /* أزرار ملوكية */
    .stButton>button {
        background-color: #004d40 !important;
        color: white !important;
        border-radius: 20px !important;
        border: none !important;
        width: 100%;
        font-weight: bold;
    }
    
    .stButton>button:hover {
        background-color: #00796b !important;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# ================= LOGIN SYSTEM =================
def login_page():
    # كود الخلفية للوجو في صفحة الدخول
    path = "static/logo.png"
    if os.path.exists(path):
        with open(path, "rb") as f:
            encoded_logo = base64.b64encode(f.read()).decode()
        
        st.markdown(f"""
            <style>
            .stApp {{
                background-image: linear-gradient(rgba(255,255,255,0.8), rgba(255,255,255,0.8)), url("data:image/png;base64,{encoded_logo}");
                background-size: contain;
                background-repeat: no-repeat;
                background-position: center;
            }}
            </style>
            """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color: #004d40;'>تسجيل الدخول</h1>", unsafe_allow_html=True)
        user = st.text_input("اسم المستخدم")
        pw = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            # يمكنك استبدال هذه القيم بملف خارجي أو قاعدة بيانات
            if user == "admin" and pw == "1234": 
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_page()
    st.stop()

# ================= SIDEBAR (LOGOUT) =================
with st.sidebar:
    st.markdown("<h2 style='color: white;'>القائمة</h2>", unsafe_allow_html=True)
    if st.button("تسجيل الخروج"):
        st.session_state["logged_in"] = False
        st.rerun()
    
    st.divider()
    mode = st.radio(
        "🌐 اختر وضع التحليل",
        ["Auto 🤖", "عربي 🇪🇬", "English 🌍"]
    )

# ================= LOGO & HEADER =================
def load_logo():
    path = "static/logo.png"
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo = load_logo()
if logo:
    st.markdown(f"""
    <div style="text-align: center;">
        <img src="data:image/png;base64,{logo}" width="300px">
    </div>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>نظام تحليل فواتير حوّلها تليكوم</h1>", unsafe_allow_html=True)

# ================= LOGIC (UNCHANGED) =================
# ... (نفس الدوال normalize, extract_numbers, clean_numbers, fix_phone, parse_ar, parse_en, parse_ai, to_excel)
# [ملاحظة: أبقِ الأكواد التي طلبتَ عدم لمسها كما هي هنا]

# ================= UPLOAD =================
st.markdown("### 📤 رفع الملفات")
files = st.file_uploader("", type=["pdf"], accept_multiple_files=True)

if files:
    if st.button("🚀 بدء المعالجة"):
        progress_bar = st.progress(0)
        all_data = []
        # ... (نفس لوجيك المعالجة الخاص بك)
        
        # محاكاة للمنطق الخاص بك لجمع البيانات (للعرض فقط هنا)
        for idx, file in enumerate(files):
            # نستخدم الكود الأصلي الخاص بك لاستخراج all_data
            # [Logic code here...]
            pass 

        # بعد المعالجة (مثال للبيانات):
        if all_data:
            df = pd.DataFrame(all_data)
            
            # --- DASHBOARD HTML/CSS ---
            st.markdown("---")
            st.markdown("<h2 style='color: #004d40; text-align: center;'>📊 لوحة البيانات الاحترافية</h2>", unsafe_allow_html=True)
            
            c1, c2, c3, c4, c5 = st.columns(5)
            
            metrics = [
                ("عدد الخطوط", len(df), "📞"),
                ("الرسوم الشهرية", f"{df['رسوم شهرية'].sum():,.2f}", "💰"),
                ("التسويات", f"{df['رسوم تسويات'].sum():,.2f}", "⚖️"),
                ("إجمالي الضرائب", f"{df['ضرائب'].sum():,.2f}", "🏛️"),
                ("الإجمالي الكلي", f"{df['إجمالي'].sum():,.2f}", "💎")
            ]
            
            cols = [c1, c2, c3, c4, c5]
            for i, (label, value, icon) in enumerate(metrics):
                with cols[i]:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 25px;">{icon}</div>
                            <div style="color: #666; font-size: 14px;">{label}</div>
                            <div style="color: #004d40; font-size: 20px; font-weight: bold;">{value}</div>
                        </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df.style.set_properties(**{'background-color': '#f9f9f9', 'color': '#004d40', 'border-color': '#004d40'}))
            
            excel = to_excel(df)
            st.download_button("📥 تحميل ملف Excel المعتمد", excel, "hawelha_report.xlsx")
