import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
import gc

# ================= 1. CONFIG & STYLES =================
st.set_page_config(page_title="Hawelha Telecom", layout="wide")

def apply_custom_design():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .stApp { background-color: #ffffff; }
    
    /* ستايل الكروت في الداش بورد */
    .dashboard-container { display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; padding: 20px; }
    .stat-card {
        background: linear-gradient(135deg, #004d40 0%, #00695c 100%);
        color: white; border-radius: 15px; padding: 25px; min-width: 220px;
        text-align: center; box-shadow: 0 10px 20px rgba(0,0,0,0.15);
        border: 1px solid #d4af37; /* لمسة ذهبية بسيطة للفخامة */
    }
    .stat-card h3 { font-size: 1.1rem; margin-bottom: 10px; opacity: 0.9; }
    .stat-card p { font-size: 1.8rem; font-weight: bold; margin: 0; }
    
    /* أزرار ملوكية */
    .stButton>button {
        background-color: #004d40 !important; color: white !important;
        border-radius: 10px !important; border: none !important;
        padding: 10px 25px !important; font-weight: bold !important; width: 100%;
    }
    .stButton>button:hover { background-color: #00251a !important; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

apply_custom_design()

# ================= 2. LOGIN LOGIC (GitHub Fix) =================
def load_users():
    try:
        # ⚠️ تأكدي أن الرابط يبدأ بـ raw.githubusercontent.com وليس github.com
        # مثال للرابط الصحيح:
        # https://raw.githubusercontent.com/USER_NAME/REPO_NAME/main/users.xlsx
        url = "رابط_ملف_اكسيل_الخام_هنا" 
        return pd.read_excel(url)
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

def login():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if not st.session_state['authenticated']:
        # عرض اللوجو في صفحة الدخول
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.image("static/logo.png", width=300) # تأكدي أن اللوجو في فولدر static
            st.markdown("<h2 style='text-align:center; color:#004d40;'>تسجيل الدخول</h2>", unsafe_allow_html=True)
            user_in = st.text_input("اسم المستخدم")
            pass_in = st.text_input("كلمة المرور", type="password")
            
            if st.button("دخول"):
                df_users = load_users()
                if df_users is not None:
                    # مطابقة اليوزر والباسورد (تأكدي من أسماء الأعمدة في ملفك)
                    match = df_users[(df_users['username'].astype(str) == user_in) & 
                                     (df_users['password'].astype(str) == pass_in)]
                    if not match.empty:
                        st.session_state['authenticated'] = True
                        st.rerun()
                    else:
                        st.error("❌ بيانات الدخول غير صحيحة")
        return False
    return True

# ================= 3. LOGIC (DO NOT MODIFY) =================
# ... (دوال استخراج البيانات الأصلية الخاصة بكِ تظل هنا كما هي) ...
def dummy_logic(): pass # Placeholder

# ================= 4. DASHBOARD (HTML Design) =================
if login():
    with st.sidebar:
        st.image("static/logo.png", width=150)
        if st.button("تسجيل الخروج"):
            st.session_state['authenticated'] = False
            st.rerun()
        st.divider()
        mode = st.radio("وضع التحليل", ["Auto 🤖", "عربي 🇪🇬", "English 🌍"])

    st.markdown("<h1 style='text-align:center; color:#004d40;'>حوّلها تليكوم - لوحة التحكم</h1>", unsafe_allow_html=True)
    
    files = st.file_uploader("ارفع الفواتير (PDF)", type=["pdf"], accept_multiple_files=True)

    if files and st.button("🚀 بدء المعالجة"):
        all_data = []
        # تنفيذ اللوجيك الخاص بك هنا لجمع البيانات في قائمة all_data
        
        if all_data:
            df = pd.DataFrame(all_data)
            
            # حساب الإجماليات
            total_lines = len(df)
            sum_monthly = df["رسوم شهرية"].sum()
            sum_settle = df["رسوم تسويات"].sum()
            sum_taxes = df["ضرائب"].sum()
            sum_total = df["إجمالي"].sum()

            # تصميم الداش بورد الاحترافي
            st.markdown(f"""
            <div class="dashboard-container">
                <div class="stat-card"><h3>عدد الخطوط</h3><p>{total_lines}</p></div>
                <div class="stat-card"><h3>الرسوم الشهرية</h3><p>{sum_monthly:,.2f}</p></div>
                <div class="stat-card"><h3>إجمالي التسويات</h3><p>{sum_settle:,.2f}</p></div>
                <div class="stat-card"><h3>إجمالي الضرائب</h3><p>{sum_taxes:,.2f}</p></div>
                <div class="stat-card"><h3>الإجمالي الكلي</h3><p>{sum_total:,.2f}</p></div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True)
            
            # زر التحميل
            # ... كود التحميل لإكسيل ...
