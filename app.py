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
    /* الخطوط والخلفية */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
    }

    .stApp {
        background-color: #ffffff;
    }

    /* تصميم الداش بورد - الكروت */
    .metric-container {
        display: flex;
        justify-content: space-around;
        gap: 10px;
        margin-bottom: 25px;
    }
    
    .metric-box {
        background: linear-gradient(145deg, #004d40, #00695c);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        flex: 1;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        border: 1px solid #c0c0c0;
    }

    .metric-box h3 {
        font-size: 1rem;
        margin-bottom: 10px;
        color: #e0e0e0;
    }

    .metric-box p {
        font-size: 1.5rem;
        font-weight: bold;
        margin: 0;
    }

    /* الأزرار */
    .stButton>button {
        background-color: #004d40 !important;
        color: white !important;
        border-radius: 8px !important;
        border: 2px solid #00251a !important;
        transition: 0.3s;
        font-weight: bold;
        width: 100%;
    }
    
    .stButton>button:hover {
        background-color: #00695c !important;
        transform: translateY(-2px);
    }

    /* القائمة الجانبية */
    [data-testid="stSidebar"] {
        background-color: #f1f8e9;
        border-left: 3px solid #004d40;
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# ================= 2. AUTHENTICATION (تسجيل الدخول) =================
def login():
    # كود الخلفية للوجو في صفحة الدخول
    path = "static/logo.png"
    logo_html = ""
    if os.path.exists(path):
        with open(path, "rb") as f:
            encoded_logo = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{encoded_logo}" width="250">'

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"<div style='text-align: center; padding: 20px;'>{logo_html}</div>", unsafe_allow_html=True)
            st.markdown("<h2 style='text-align: center; color: #004d40;'>تسجيل الدخول للنظام</h2>", unsafe_allow_html=True)
            
            user = st.text_input("اسم المستخدم", placeholder="Admin")
            password = st.text_input("كلمة المرور", type="password", placeholder="****")
            
            if st.button("دخول"):
                # عدل اليوزر والباسورد هنا
                if user == "hawelha" and password == "2026":
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("بيانات الدخول غير صحيحة")
        return False
    return True

# ================= 3. UTILS & LOGIC (بدون تعديل المنطق) =================
def normalize(t):
    return (t or "").replace("−","-").replace("–","-").replace("—","-")

def extract_numbers(text):
    if not text: return []
    text = normalize(str(text))
    text = re.sub(r'\((\d+\.?\d*)\)', r'-\1', text)
    text = re.sub(r'(\d+\.?\d*)-', r'-\1', text)
    text = re.sub(r'-\s+(\d)', r'-\1', text)
    numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
    return [float(n) for n in numbers]

def clean_numbers(vals, phone):
    phone_int = str(int(phone))
    return [v for v in vals if str(int(v)) != phone_int]

def fix_phone(phone):
    phone = str(phone)
    if len(phone) == 10 and phone.startswith("1"):
        return "0" + phone
    return phone

def parse_ar(file):
    records = []
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
                        phone = phone.group(1)
                        vals = extract_numbers(text)
                        if i+1 < len(table):
                            nxt = extract_numbers(" ".join([str(c) for c in table[i+1] if c]))
                            if len(nxt) > len(vals): vals = nxt; i += 1
                        vals = clean_numbers(vals, phone)
                        vals = vals[::-1]
                        def g(idx): return vals[idx] if idx < len(vals) else 0
                        records.append({
                            "محمول": phone, "رسوم شهرية": g(0), "رسوم الخدمات": g(1),
                            "مكالمات محلية": g(2), "رسائل محلية": g(3), "إنترنت محلية": g(4),
                            "مكالمات دولية": g(5), "رسائل دولية": g(6), "مكالمات تجوال": g(7),
                            "رسائل تجوال": g(8), "إنترنت تجوال": g(9), "رسوم تسويات": g(10),
                            "ضرائب": g(11), "إجمالي": g(12),
                        })
                    i += 1
    return records

def parse_en(file):
    records = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages[2:]:
            for table in page.extract_tables() or []:
                i = 0
                while i < len(table):
                    row = table[i]
                    if not row: i += 1; continue
                    text = " ".join([str(c) for c in row])
                    phone = re.search(r'(01[0125]\d{8})', text)
                    if phone:
                        phone = phone.group(1)
                        vals = extract_numbers(" ".join([str(c) for c in table[i+1] if c]) if i+1 < len(table) else "")
                        vals = clean_numbers(vals, phone)
                        records.append({
                            "محمول": phone, "رسوم شهرية": vals[0] if len(vals)>0 else 0,
                            "رسوم الخدمات": vals[1] if len(vals)>1 else 0, "مكالمات محلية": vals[2] if len(vals)>2 else 0,
                            "رسائل محلية": vals[3] if len(vals)>3 else 0, "إنترنت محلية": vals[4] if len(vals)>4 else 0,
                            "مكالمات دولية": vals[5] if len(vals)>5 else 0, "رسائل دولية": vals[6] if len(vals)>6 else 0,
                            "مكالمات تجوال": vals[7] if len(vals)>7 else 0, "رسائل تجوال": vals[8] if len(vals)>8 else 0,
                            "إنترنت تجوال": vals[9] if len(vals)>9 else 0, "رسوم تسويات": vals[10] if len(vals)>10 else 0,
                            "ضرائب": vals[11] if len(vals)>11 else 0, "إجمالي": vals[-1] if vals else 0
                        })
                        i += 2; continue
                    i += 1
    return records

def parse_ai(file):
    records = []
    try:
        with pdfplumber.open(file) as pdf:
            text = "".join([normalize(p.extract_text() or "") for p in pdf.pages])
        phone_match = re.search(r'(01[0125]\d{8}|\b1[0125]\d{8}\b)', text)
        if not phone_match: return []
        phone = fix_phone(phone_match.group(1))
        def get_v(pattern):
            m = re.search(pattern, text)
            return float(m.group(1)) if m else 0
        monthly = get_v(r'إجمالي الرسوم الشهرية.*?(\d+\.\d+)')
        tax = sum([get_v(p) for p in [r'ضريبة الجدول.*?(\d+\.\d+)', r'ضريبة القيمة المضافة.*?(\d+\.\d+)', r'ضريبة الدمغة.*?(\d+\.\d+)', r'تنمية موارد الدولة.*?(\d+\.\d+)']])
        total = get_v(r'إجمالي القيمة المستحقة.*?(\d+\.\d+)')
        records.append({
            "محمول": phone, "رسوم شهرية": monthly, "رسوم الخدمات": 0, "مكالمات محلية": 0, "رسائل محلية": 0,
            "إنترنت محلية": 0, "مكالمات دولية": 0, "رسائل دولية": 0, "مكالمات تجوال": 0, "رسائل تجوال": 0,
            "إنترنت تجوال": 0, "رسوم تسويات": 0, "ضرائب": round(tax, 2), "إجمالي": total
        })
    except: return []
    return records

def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    out.seek(0)
    return out

# ================= 4. MAIN INTERFACE =================
if login():
    # زر تسجيل الخروج
    with st.sidebar:
        st.markdown(f"<h3 style='color: #004d40;'>مرحباً بك</h3>", unsafe_allow_html=True)
        if st.button("🚪 تسجيل الخروج"):
            st.session_state['logged_in'] = False
            st.rerun()
        
        st.divider()
        mode = st.radio("🌐 وضع التحليل", ["Auto 🤖", "عربي 🇪🇬", "English 🌍"], horizontal=True)

    # الهيدر واللوجو
    path = "static/logo.png"
    if os.path.exists(path):
        with open(path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_b64}" width="200"></div>', unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center; color: #004d40; margin-top: -20px;'>لوحة التحكم الذكية</h1>", unsafe_allow_html=True)

    # رفع الملفات
    files = st.file_uploader("قم برفع فواتير PDF هنا", type=["pdf"], accept_multiple_files=True)

    if files:
        if st.button("🚀 معالجة البيانات الآن"):
            progress_bar = st.progress(0)
            all_data = []
            failed = []

            for idx, file in enumerate(files):
                try:
                    progress_bar.progress(int(((idx + 1) / len(files)) * 100))
                    # اكتشاف اللغة
                    if mode == "Auto 🤖":
                        with pdfplumber.open(file) as pdf:
                            text_check = pdf.pages[0].extract_text() or ""
                        lang = "ar" if re.search(r'[\u0600-\u06FF]', text_check) else "en"
                    else:
                        lang = "ar" if mode == "عربي 🇪🇬" else "en"

                    # التحليل
                    data = parse_ar(file) if lang == "ar" else parse_en(file)
                    if not data: data = parse_ai(file)
                    if data: all_data.extend(data)
                except:
                    failed.append(file.name)
                gc.collect()

            if all_data:
                df = pd.DataFrame(all_data)
                
                # إجمالي الحسابات
                total_lines = len(df)
                total_monthly = df["رسوم شهرية"].sum()
                total_settlements = df["رسوم تسويات"].sum()
                total_taxes = df["ضرائب"].sum()
                total_grand = df["إجمالي"].sum()

                # عرض الداش بورد (HTML)
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-box"><h3>عدد الخطوط</h3><p>{total_lines}</p></div>
                    <div class="metric-box"><h3>الرسوم الشهرية</h3><p>{total_monthly:,.2f}</p></div>
                    <div class="metric-box"><h3>التسويات</h3><p>{total_settlements:,.2f}</p></div>
                    <div class="metric-box"><h3>إجمالي الضرائب</h3><p>{total_taxes:,.2f}</p></div>
                    <div class="metric-box"><h3>الإجمالي الكلي</h3><p>{total_grand:,.2f}</p></div>
                </div>
                """, unsafe_allow_html=True)

                # عرض الجدول
                st.markdown("<h3 style='color: #004d40;'>📋 معاينة البيانات المستخرجة</h3>", unsafe_allow_html=True)
                st.dataframe(df.style.highlight_max(axis=0, color='#e8f5e9'), use_container_width=True)

                # التحميل
                excel_file = to_excel(df)
                st.download_button(
                    label="📥 تحميل تقرير Excel النهائي",
                    data=excel_file,
                    file_name="Hawelha_Full_Report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                if failed:
                    st.warning(f"⚠️ الملفات التي لم يتم التعرف عليها: {failed}")
            else:
                st.error("لم يتم استخراج أي بيانات، تأكد من جودة ملفات PDF.")
