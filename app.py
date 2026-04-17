import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
import gc

# ================= 1. CONFIG & ROYAL STYLE =================
st.set_page_config(page_title="Hawelha Telecom | حوّلها تليكوم", page_icon="📊", layout="wide")

def apply_royal_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* الأساسيات */
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .stApp { background-color: #F8F9FA; }
    
    /* إخفاء القوائم الافتراضية لزيادة الفخامة */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* صندوق تسجيل الدخول */
    .login-card {
        background: white;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        border-top: 6px solid #004d40;
        margin-top: 50px;
    }

    /* هيدر الداش بورد */
    .main-header {
        background: linear-gradient(135deg, #004d40 0%, #00796b 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,77,64,0.2);
    }

    /* بطاقات الإحصائيات الملوكية */
    .metric-container {
        display: flex;
        justify-content: space-between;
        gap: 15px;
        margin-bottom: 25px;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        flex: 1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        border: 1px solid #E0E0E0;
        transition: transform 0.3s ease;
    }
    .metric-card:hover { transform: translateY(-5px); border-color: #004d40; }
    .metric-label { color: #666; font-size: 14px; margin-bottom: 5px; }
    .metric-value { color: #004d40; font-size: 24px; font-weight: bold; }

    /* الأزرار */
    div.stButton > button {
        background: linear-gradient(to right, #004d40, #00796b) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 10px 25px !important;
        font-weight: bold !important;
        width: 100%;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        box-shadow: 0 5px 15px rgba(0,77,64,0.3) !important;
        opacity: 0.9;
    }

    /* Sidebar Customization */
    [data-testid="stSidebar"] { background-color: white; border-left: 1px solid #EEE; }
    
    </style>
    """, unsafe_allow_html=True)

apply_royal_theme()

# ================= 2. DATA LOAD & AUTH =================
# قراءة ملف المستخدمين مع التعامل مع الأخطاء
try:
    df_users = pd.read_excel("users.xlsx")
    users = {
        str(row["Username"]): {
            "password": str(row["Password"]),
            "role": row["Role"]
        }
        for _, row in df_users.iterrows()
    }
except Exception as e:
    st.error("⚠️ فشل تحميل ملف users.xlsx. تأكد من وجوده في المجلد الرئيسي.")
    st.stop()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_screen():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        # إذا كان لديك لوجو، يمكنك إضافته هنا
        # st.image("logo.png", width=150) 
        st.markdown("<h2 style='text-align:center; color:#004d40;'>🔐 بوابة حوّلها تليكوم</h2>", unsafe_allow_html=True)
        
        user_input = st.text_input("اسم المستخدم", key="user")
        pass_input = st.text_input("كلمة المرور", type="password", key="pass")
        
        if st.button("تسجيل الدخول"):
            if user_input in users and users[user_input]["password"] == pass_input:
                st.session_state.logged_in = True
                st.session_state.username = user_input
                st.session_state.role = users[user_input]["role"]
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة")
        st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.logged_in:
    login_screen()
    st.stop()

# ================= 3. APP HEADER & SIDEBAR =================
with st.sidebar:
    st.markdown(f"### 👤 مرحباً، {st.session_state.username}")
    st.info(f"الرتبة: {st.session_state.role}")
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.logged_in = False
        st.rerun()
    st.divider()
    mode = st.radio("🌐 وضع التحليل", ["Auto 🤖", "عربي 🇪🇬", "English 🌍"], horizontal=False)

st.markdown('<div class="main-header"><h1>📊 لوحة التحكم الذكية - Hawelha Telecom</h1></div>', unsafe_allow_html=True)

# ================= 4. ADMIN PANEL =================
if st.session_state.role == "admin":
    with st.expander("⚙️ إدارة النظام (للمشرفين فقط)"):
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي المستخدمين", len(df_users))
        c2.metric("المشرفين", len(df_users[df_users["Role"]=="admin"]))
        c3.metric("المستخدمين العاديين", len(df_users[df_users["Role"]=="user"]))
        st.dataframe(df_users, use_container_width=True)

# ================= 5. LOGIC (DO NOT MODIFY) =================
def normalize(t): return (t or "").replace("−","-").replace("–","-").replace("—","-")

def extract_numbers(text):
    if not text: return []
    text = normalize(str(text))
    text = re.sub(r'\((\d+\.?\d*)\)', r'-\1', text)
    text = re.sub(r'(\d+\.?\d*)-', r'-\1', text)
    text = re.sub(r'-\s+(\d)', r'-\1', text)
    return [float(n) for n in re.findall(r'-?\d+(?:\.\d+)?', text)]

def clean_numbers(vals, phone):
    p_int = str(int(phone))
    return [v for v in vals if str(int(v)) != p_int]

def fix_phone(phone):
    phone = str(phone)
    return "0" + phone if (len(phone) == 10 and phone.startswith("1")) else phone

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
                        phone = phone.group(1); vals = extract_numbers(text)
                        if i+1 < len(table):
                            nxt = extract_numbers(" ".join([str(c) for c in table[i+1] if c]))
                            if len(nxt) > len(vals): vals = nxt; i += 1
                        vals = clean_numbers(vals, phone)[::-1]
                        g = lambda x: vals[x] if x < len(vals) else 0
                        records.append({
                            "محمول": phone, "رسوم شهرية": g(0), "رسوم الخدمات": g(1), "مكالمات محلية": g(2),
                            "رسائل محلية": g(3), "إنترنت محلية": g(4), "مكالمات دولية": g(5), "رسائل دولية": g(6),
                            "مكالمات تجوال": g(7), "رسائل تجوال": g(8), "إنترنت تجوال": g(9), "رسوم تسويات": g(10),
                            "ضرائب": g(11), "إجمالي": g(12)
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
                    text = " ".join([str(c) for c in row]); phone = re.search(r'(01[0125]\d{8})', text)
                    if phone:
                        phone = phone.group(1)
                        vals = extract_numbers(" ".join([str(c) for c in table[i+1] if c]) if i+1 < len(table) else "")
                        vals = clean_numbers(vals, phone)
                        g = lambda x: vals[x] if x < len(vals) else 0
                        records.append({
                            "محمول": phone, "رسوم شهرية": g(0), "رسوم الخدمات": g(1), "مكالمات محلية": g(2),
                            "رسائل محلية": g(3), "إنترنت محلية": g(4), "مكالمات دولية": g(5), "رسائل دولية": g(6),
                            "مكالمات تجوال": g(7), "رسائل تجوال": g(8), "إنترنت تجوال": g(9), "رسوم تسويات": g(10),
                            "ضرائب": g(11), "إجمالي": vals[-1] if vals else 0
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
        def get_v(p):
            m = re.search(p, text)
            return float(m.group(1)) if m else 0
        tax = sum([get_v(r) for r in [r'ضريبة الجدول.*?(\d+\.\d+)', r'ضريبة القيمة المضافة.*?(\d+\.\d+)', r'ضريبة الدمغة.*?(\d+\.\d+)', r'تنمية موارد الدولة.*?(\d+\.\d+)']])
        records.append({
            "محمول": phone, "رسوم شهرية": get_v(r'إجمالي الرسوم الشهرية.*?(\d+\.\d+)'), "رسوم الخدمات": 0,
            "ضرائب": round(tax, 2), "إجمالي": get_v(r'إجمالي القيمة المستحقة.*?(\d+\.\d+)')
        })
    except: return []
    return records

def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w: df.to_excel(w, index=False)
    out.seek(0)
    return out

# ================= 6. MAIN INTERFACE =================
st.markdown("### 📤 رفع وتحميل الملفات")
files = st.file_uploader("", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")

if files:
    if st.button("🚀 بدء معالجة الفواتير"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        all_data = []

        for idx, file in enumerate(files):
            status_text.markdown(f"**جاري معالجة:** `{file.name}`")
            progress_bar.progress((idx + 1) / len(files))
            
            data = parse_ar(file) if mode != "English 🌍" else parse_en(file)
            if not data: data = parse_ai(file)
            all_data.extend(data)
            gc.collect()

        if all_data:
            df = pd.DataFrame(all_data).fillna(0)
            
            # عرض الداش بورد الملوكي
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card"><div class="metric-label">📱 عدد الخطوط</div><div class="metric-value">{len(df)}</div></div>
                <div class="metric-card"><div class="metric-label">💰 الرسوم الشهرية</div><div class="metric-value">{df['رسوم شهرية'].sum():,.2f}</div></div>
                <div class="metric-card"><div class="metric-label">🧾 إجمالي الضرائب</div><div class="metric-value">{df['ضرائب'].sum():,.2f}</div></div>
                <div class="metric-card"><div class="metric-label">📊 الإجمالي النهائي</div><div class="metric-value">{df['إجمالي'].sum():,.2f}</div></div>
            </div>
            """, unsafe_allow_html=True)

            st.success("🎉 اكتملت المعالجة بنجاح!")
            st.dataframe(df, use_container_width=True)
            
            # زر التحميل
            col_d1, col_d2, col_d3 = st.columns([1,2,1])
            with col_d2:
                st.download_button("📥 تحميل التقرير النهائي (Excel)", to_excel(df), "Hawelha_Telecom_Report.xlsx")
        else:
            st.error("لم يتم العثور على بيانات صالحة في الملفات.")

# ================= 7. FOOTER =================
st.markdown(f"""
<br><hr>
<div style='text-align:center; color:#999; font-size:14px;'>
© 2026 حوّلها تليكوم — بواسطة نجاة البكري | جميع الحقوق محفوظة
</div>
""", unsafe_allow_html=True)
