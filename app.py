import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
import gc

# ================= 1. CONFIG & ROYAL STYLE =================
# قمنا بتغيير العنوان ليتناسب مع التصميم الجديد الفخم
st.set_page_config(page_title="Hawelha System | Convert PDF to Excel", page_icon="📊", layout="wide")

def apply_elite_theme():
    # تصميم CSS مخصص لمحاكاة الصورة الأخيرة (الفخامة والتنظيم)
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    
    /* الأساسيات وتغيير الخط لـ Poppins للمظهر العصري */
    * { font-family: 'Poppins', sans-serif; }
    .stApp { background-color: #F0F2F5; } /* خلفية رمادية فاتحة جداً لإبراز البطاقات */
    
    /* إخفاء عناصر سترمليت الافتراضية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* صندوق تسجيل الدخول الفخم */
    .login-box {
        background: white;
        padding: 50px;
        border-radius: 25px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.08);
        border-top: 8px solid #004d40;
        margin-top: 50px;
        text-align: center;
    }

    /* الهيدر الجديد (بدون الخلفية الخضراء وبدون الخط الفاصل) */
    .elite-header {
        text-align: center;
        margin-bottom: 40px;
        padding: 20px 0;
    }
    .elite-header h1 {
        color: #004d40;
        font-weight: 700;
        font-size: 2.5rem;
        margin: 0;
    }
    .elite-header p {
        color: #666;
        font-size: 1.1rem;
        margin-top: 10px;
    }

    /* تصميم البطاقات (Cards) لمحاكاة الصورة الأخيرة */
    .elite-card {
        background: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.04);
        margin-bottom: 25px;
        border: 1px solid #EAEAEA;
    }
    .card-title {
        color: #004d40;
        font-weight: 600;
        font-size: 1.3rem;
        margin-bottom: 20px;
        border-right: 5px solid #004d40; /* لمسة جمالية على اليمين للملف العربي */
        padding-right: 15px;
    }

    /* بطاقات الداش بورد (Data Overview) */
    .metric-card-elite {
        background: #F8F9FA;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        border: 1px solid #EEE;
    }
    .metric-label-elite { color: #888; font-size: 14px; margin-bottom: 5px; }
    .metric-value-elite { color: #004d40; font-size: 28px; font-weight: 700; }

    /* الأزرار الخضراء الموحدة والفخمة */
    div.stButton > button {
        background: linear-gradient(135deg, #004d40 0%, #00695c 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 12px 30px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        width: 100%;
        transition: all 0.3s ease-in-out;
    }
    div.stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(0,77,64,0.2) !important;
    }
    
    /* تنسيق خاص لزر تسجيل الخروج */
    .st_logout_btn button {
        background: #f8d7da !important;
        color: #721c24 !important;
        border: 1px solid #f5c6cb !important;
    }
    
    /* تنسيق قائمة الخيارات (Radio) */
    div[data-testid="stRadio"] > label { font-weight: 600; color: #004d40; }
    div[data-testid="stRadio"] label { font-size: 1rem; }

    </style>
    """, unsafe_allow_html=True)

apply_elite_theme()

# ================= 2. AUTHENTICATION (قراءة من ملف Excel) =================
# دالة لجلب البيانات الخام من GitHub لتجنب خطأ 404
@st.cache_data(ttl=600, show_spinner=False) # كاش لمدة 10 دقائق لسرعة الأداء
def load_github_users():
    try:
        # ⚠️ استبدل هذا الرابط برابط RAW الخاص بملف users.xlsx على GitHub
        raw_url = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/users.xlsx"
        df = pd.read_excel(raw_url)
        return df
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

def login_screen():
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        # اللوجو
        if os.path.exists("static/logo.png"):
            st.image("static/logo.png", width=250)
        
        st.markdown("<h1 style='color:#004d40; margin-bottom:10px;'>Secure Login</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#777; margin-bottom:30px;'>Please enter your credentials to access Hawelha System</p>", unsafe_allow_html=True)
        
        u_in = st.text_input("Username", key="u_field", placeholder="e.g. noga")
        p_in = st.text_input("Password", type="password", key="p_field", placeholder="••••••••")
        
        if st.button("Login to System"):
            df_users = load_github_users()
            if df_users is not None:
                # التأكد من أسماء الأعمدة username و password في ملف الإكسيل
                user_match = df_users[(df_users['username'].astype(str) == u_in) & 
                                      (df_users['password'].astype(str) == p_in)]
                
                if not user_match.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = u_in
                    st.session_state['role'] = user_match.iloc[0]['role']
                    st.rerun()
                else:
                    st.error("❌ Invalid Username or Password")
        st.markdown('</div>', unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_screen()
    st.stop()

# ================= 3. SYSTEM INTERFACE (بعد تسجيل الدخول) =================
# الهيدر الجديد الفخم (تم حل مشكلة الخط الفاصل وتغيير الجملة)
st.markdown("""
<div class="elite-header">
    <h1>Hawelha System</h1>
    <p>Convert PDF invoices to Excel instantly</p>
</div>
""", unsafe_allow_html=True)

# الشريط الجانبي (Sidebar) مصمم ليكون أنيقاً
with st.sidebar:
    st.markdown(f"""
    <div style='text-align: center; padding: 20px; border-bottom: 1px solid #EEE;'>
        <div style='font-size: 20px; font-weight: 600; color: #004d40;'>Welcome,</div>
        <div style='font-size: 18px; color: #555;'>{st.session_state['username']}!</div>
        <div style='background: #e0f2f1; color: #004d40; padding: 3px 10px; border-radius: 20px; font-size: 12px; display: inline-block; margin-top: 5px;'>{st.session_state['role']}</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # وضع التحليل
    st.markdown("<div class='card-title'>Analysis Mode</div>", unsafe_allow_html=True)
    mode = st.radio("", ["Auto 🤖", "عربي 🇪🇬", "English 🌍"], label_visibility="collapsed")
    
    st.markdown("<br><hr>", unsafe_allow_html=True)
    # زر تسجيل الخروج
    if st.button("Log out", key="logout_btn", help="Securely sign out"):
        st.session_state['logged_in'] = False
        st.rerun()

# ================= 4. LOGIC (UNCHANGED - طلبتِ عدم لمسه) =================
# سأبقي الدوال normalize, extract_numbers, clean_numbers, fix_phone, parse_ar, parse_en, parse_ai كما هي تماماً.
# [نضع الدوال الأصلية هنا]
# =========================================================================

# ================= 5. MAIN CONTENT (LAYOUT SIMILAR TO FINAL IMAGE) =================
# تقسيم الصفحة لعمودين لمحاكاة تصميم الصورة الأخيرة
col_main1, col_main2 = st.columns([1, 1.3], gap="large")

with col_main1:
    # بطاقة رفع الملفات (Upload)
    st.markdown('<div class="elite-card">', unsafe_allow_html=True)
    st.markdown("<div class='card-title'>Upload PDF Files</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; padding: 20px 0;'><img src='https://cdn-icons-png.flaticon.com/512/337/337946.png' width='100'></div>", unsafe_allow_html=True) # أيقونة PDF للجمال
    files = st.file_uploader("Upload PDF Files", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

with col_main2:
    # بطاقة عرض البيانات (Data Overview)
    # سيتم عرضها فقط بعد المعالجة
    data_overview_placeholder = st.empty()

# ================= 6. PROCESSING & DASHBOARD =================
if files:
    # وضع زر المعالجة داخل بطاقة الرفع
    with col_main1:
        start_btn = st.button("🚀 Convert to Excel")

    if start_btn:
        progress_bar = st.progress(0)
        status_text = st.empty()
        all_data = []

        # محاكاة المعالجة باستخدام اللوجيك الأصلي الخاص بكِ
        for idx, file in enumerate(files):
            # [تطبيق اللوجيك الخاص بكِ هنا...]
            pass # placeholder
        
        # [افترض أننا حصلنا على df]
        # مثال لبيانات للعرض (يجب استبدالها بالبيانات الحقيقية من اللوجيك)
        data_example = {
            "محمول": ["01001234567", "01123456789"],
            "رسوم شهرية": [100.5, 200.0],
            "ضرائب": [14.0, 28.0],
            "إجمالي": [114.5, 228.0]
        }
        df = pd.DataFrame(data_example)

        progress_bar.progress(100)
        st.success("🎉 Conversion Complete!")

        # ملء داش بورد "Data Overview" (col_main2)
        with col_main2:
            st.markdown('<div class="elite-card">', unsafe_allow_html=True)
            st.markdown("<div class='card-title'>Data Overview</div>", unsafe_allow_html=True)
            
            # كروت الإحصائيات (Metrics)
            stat1, stat2, stat3 = st.columns(3)
            with stat1:
                st.markdown(f"<div class='metric-card-elite'><div class='metric-label-elite'>Lines</div><div class='metric-value-elite'>{len(df)}</div></div>", unsafe_allow_html=True)
            with stat2:
                st.markdown(f"<div class='metric-card-elite'><div class='metric-label-elite'>Avg Monthly</div><div class='metric-value-elite'>{df['رسوم شهرية'].mean():,.2f}</div></div>", unsafe_allow_html=True)
            with stat3:
                st.markdown(f"<div class='metric-card-elite'><div class='metric-label-elite'>Total Amount</div><div class='metric-value-elite'>{df['إجمالي'].sum():,.2f}</div></div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            # عرض جدول معاينة
            st.dataframe(df.head(10), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # بطاقة تحميل التقرير (Download)
        st.markdown('<div class="elite-card">', unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Download Report</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; padding: 20px 0;'><img src='https://cdn-icons-png.flaticon.com/512/732/732220.png' width='100'></div>", unsafe_allow_html=True) # أيقونة إكسيل
        
        # [استخدام دالة to_excel الأصلية...]
        st.download_button(
            label="📥 Download Excel File",
            data=b"placeholder", # out_excel.getvalue()
            file_name="Hawelha_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.markdown('</div>', unsafe_allow_html=True)

# ================= 7. FOOTER =================
st.markdown("""
<br><hr>
<div style='text-align:center;color:#777;font-size:14px;'>
© 2026 Najat El Bakry — All Rights Reserved.
</div>
""", unsafe_allow_html=True)
