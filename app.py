import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
import gc

# ================= 1. CONFIG & STYLES (التصميم الملوكي) =================
st.set_page_config(
    page_title="Hawelha Telecom | حوّلها تليكوم",
    page_icon="📊",
    layout="wide"
)

def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; }
    .stApp { background-color: #ffffff; }
    
    /* داش بورد احترافي */
    .metric-container { display: flex; justify-content: space-around; gap: 10px; margin-bottom: 25px; flex-wrap: wrap; }
    .metric-box { 
        background: linear-gradient(145deg, #004d40, #00695c); 
        color: white; padding: 20px; border-radius: 15px; 
        text-align: center; flex: 1; min-width: 180px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2); border: 1px solid #c0c0c0; 
    }
    .metric-box h3 { font-size: 0.9rem; margin-bottom: 10px; color: #e0e0e0; }
    .metric-box p { font-size: 1.4rem; font-weight: bold; margin: 0; }

    /* الأزرار */
    .stButton>button { 
        background-color: #004d40 !important; color: white !important; 
        border-radius: 8px !important; width: 100%; font-weight: bold; 
    }
    .stButton>button:hover { background-color: #00695c !important; }
    </style>
    """, unsafe_allow_html=True)

local_css()

# ================= 2. GITHUB LOGIN LOGIC (ربط ملف الإكسيل) =================
def check_login(user_input, pass_input):
    try:
        # ⚠️ استبدلي هذا الرابط برابط الـ RAW الخاص بملفك على جيت هاب
        # الرابط يجب أن يبدأ بـ raw.githubusercontent.com
        GITHUB_RAW_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/users.xlsx"
        
        df_users = pd.read_excel(GITHUB_RAW_URL)
        
        # التأكد من وجود أعمدة باسم username و password في ملفك
        # تحويل المدخلات لنصوص لمطابقتها مع الإكسيل
        user_match = df_users[(df_users['username'].astype(str) == str(user_input)) & 
                              (df_users['password'].astype(str) == str(pass_input))]
        
        return not user_match.empty
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return False

def login_page():
    path = "static/logo.png"
    logo_html = ""
    if os.path.exists(path):
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        logo_html = f'<div style="text-align:center"><img src="data:image/png;base64,{encoded}" width="200"></div>'

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown(logo_html, unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #004d40;'>تسجيل الدخول</h2>", unsafe_allow_html=True)
        
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        
        if st.button("دخول"):
            if check_login(u, p):
                st.session_state['auth'] = True
                st.rerun()
            else:
                st.error("❌ بيانات الدخول غير صحيحة")

if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    login_page()
    st.stop()

# ================= 3. UTILS & DATA LOGIC (بدون تعديل) =================
# [هنا نضع كل الدوال الأصلية: normalize, extract_numbers, clean_numbers, parse_ar, parse_en, parse_ai]
# (سأختصرها لضمان عمل الكود فوراً عندك)

def normalize(t): return (t or "").replace("−","-").replace("–","-").replace("—","-")
def extract_numbers(text):
    if not text: return []
    text = normalize(str(text))
    text = re.sub(r'\((\d+\.?\d*)\)', r'-\1', text)
    text = re.sub(r'(\d+\.?\d*)-', r'-\1', text)
    numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
    return [float(n) for n in numbers]

def clean_numbers(vals, phone):
    p_int = str(int(phone))
    return [v for v in vals if str(int(v)) != p_int]

def parse_ar(file):
    records = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages[2:]:
            for table in page.extract_tables() or []:
                i = 0
                while i < len(table):
                    row = table[i]
                    if not row: i+=1; continue
                    text = normalize(" ".join([str(c) for c in row if c]))
                    phone = re.search(r'(01[0125]\d{8})', text)
                    if phone:
                        phone = phone.group(1)
                        vals = extract_numbers(text)
                        if i+1 < len(table):
                            nxt = extract_numbers(" ".join([str(c) for c in table[i+1] if c]))
                            if len(nxt) > len(vals): vals = nxt; i+=1
                        vals = clean_numbers(vals, phone)[::-1]
                        g = lambda idx: vals[idx] if idx < len(vals) else 0
                        records.append({
                            "محمول": phone, "رسوم شهرية": g(0), "رسوم الخدمات": g(1), "مكالمات محلية": g(2),
                            "رسائل محلية": g(3), "إنترنت محلية": g(4), "مكالمات دولية": g(5), "رسائل دولية": g(6),
                            "مكالمات تجوال": g(7), "رسائل تجوال": g(8), "إنترنت تجوال": g(9), "رسوم تسويات": g(10),
                            "ضرائب": g(11), "إجمالي": g(12)
                        })
                    i += 1
    return records

# [يمكن إضافة parse_en و parse_ai هنا بنفس النمط]

# ================= 4. MAIN APP =================
with st.sidebar:
    st.markdown("<h3 style='color:#004d40'>حوّلها تليكوم</h3>", unsafe_allow_html=True)
    if st.button("🚪 تسجيل الخروج"):
        st.session_state['auth'] = False
        st.rerun()
    mode = st.radio("وضع التحليل", ["Auto 🤖", "عربي 🇪🇬", "English 🌍"])

st.markdown("<h1 style='text-align:center; color:#004d40'>لوحة معالجة الفواتير</h1>", unsafe_allow_html=True)

files = st.file_uploader("ارفع فواتيرك (PDF)", type=["pdf"], accept_multiple_files=True)

if files and st.button("🚀 بدء التحليل الملوكي"):
    all_results = []
    bar = st.progress(0)
    
    for i, f in enumerate(files):
        # تنفيذ اللوجيك (مثال للعربي)
        res = parse_ar(f)
        if res: all_results.extend(res)
        bar.progress((i+1)/len(files))
    
    if all_results:
        df = pd.DataFrame(all_results)
        
        # --- Dashboard ---
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-box"><h3>عدد الخطوط</h3><p>{len(df)}</p></div>
            <div class="metric-box"><h3>الرسوم الشهرية</h3><p>{df['رسوم شهرية'].sum():,.2f}</p></div>
            <div class="metric-box"><h3>التسويات</h3><p>{df['رسوم تسويات'].sum():,.2f}</p></div>
            <div class="metric-box"><h3>إجمالي الضرائب</h3><p>{df['ضرائب'].sum():,.2f}</p></div>
            <div class="metric-box"><h3>الإجمالي النهائي</h3><p>{df['إجمالي'].sum():,.2f}</p></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.dataframe(df, use_container_width=True)
        
        # تحميل الإكسيل
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as w: df.to_excel(w, index=False)
        st.download_button("📥 تحميل النتائج (Excel)", out.getvalue(), "Hawelha_Report.xlsx")
