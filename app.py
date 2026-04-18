import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
import gc

# ================= CONFIG =================
st.set_page_config(page_title="Hawelha Telecom", layout="wide", page_icon="📊")

# ================= STYLE & THEME =================
PRIMARY_COLOR = "#0B6B3A"  # Royal Green
BG_COLOR = "#F4F6F8"
CARD_BG = "#FFFFFF"

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');

    .stApp {
        background-color: #F4F6F8;
        font-family: 'Tajawal', sans-serif;
    }

    /* Hide Default Streamlit Elements */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    /* === LOGIN PAGE BACKGROUND - FULL LOGO VISIBILITY === */
    .login-background {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: #F4F6F8;
        z-index: -1;
    }

    /* Glassmorphism Card for Login Form */
    .login-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        max-width: 400px;
        margin: 80px auto;
        text-align: center;
    }

    .login-title {
        color: #0B6B3A;
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 25px;
    }

    /* === DASHBOARD HEADER DESIGN === */
    .dashboard-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: white;
        padding: 15px 30px;
        border-radius: 0 0 20px 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 30px;
        border-bottom: 4px solid #0B6B3A;
    }

    .header-main-text {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
    }

    .header-main-text h1 {
        margin: 0;
        font-size: 26px;
        color: #0B6B3A;
        font-weight: 800;
        letter-spacing: 0.5px;
    }

    .header-logo {
        width: 220px;
        max-width: 100%;
        height: auto;
        display: block;
        object-fit: contain;
    }

    .header-user-info {
        display: flex;
        align-items: center;
        gap: 15px;
        background: #f0fdf4;
        padding: 8px 20px;
        border-radius: 50px;
        border: 1px solid #dcfce7;
    }

    .user-avatar {
        width: 35px;
        height: 35px;
        background: #0B6B3A;
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 16px;
    }

    .user-name {
        font-weight: 600;
        color: #333;
        font-size: 16px;
    }

    /* Metric Cards Styling */
    .metric-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-right: 5px solid #0B6B3A;
        transition: transform 0.2s;
        height: 100%;
    }

    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }

    .metric-title {
        color: #666;
        font-size: 15px;
        font-weight: 500;
        margin-bottom: 10px;
    }

    .metric-value {
        color: #0B6B3A;
        font-size: 26px;
        font-weight: 700;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #888;
        font-size: 12px;
        margin-top: 50px;
        padding: 20px;
        border-top: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# ================= USERS DATA LOADING =================
try:
    df_users = pd.read_excel("users.xlsx")
    users = {
        row["Username"]: {
            "password": str(row["Password"]),
            "role": row["Role"]
        }
        for _, row in df_users.iterrows()
    }
except FileNotFoundError:
    st.error("ملف users.xlsx غير موجود. يرجى التأكد من وجوده في نفس المجلد.")
    st.stop()

# ================= SESSION STATE INIT =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "show_admin_panel" not in st.session_state:
    st.session_state.show_admin_panel = False

# ================= LOGIN FUNCTION =================
def login_page():
    st.markdown('<div class="login-background"></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-card">
            <div class="login-title">
                🔐 تسجيل الدخول
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        username = st.text_input("اسم المستخدم", placeholder="اسم المستخدم 👤", label_visibility="hidden")
        password = st.text_input("كلمة المرور", placeholder="كلمة المرور 🔒", type="password", label_visibility="hidden")  
        
        if st.button("تسجيل الدخول", use_container_width=True):
            if username in users and users[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = users[username]["role"]
                st.session_state.show_admin_panel = False
                st.rerun()
            else:
                st.error("⚠️ بيانات الدخول غير صحيحة")
                
# ================= MAIN APP LOGIC =================
if not st.session_state.logged_in:
    login_page()
    st.stop()

# ================= SECURITY FOR ADMIN PANEL =================
if st.session_state.get("role") != "admin":
    st.session_state.show_admin_panel = False

# ================= DASHBOARD HEADER =================
user_initial = st.session_state.username[0].upper() if st.session_state.username else "?"
logo_url = "https://raw.githubusercontent.com/najat2030/hawelha-telecom-app/main/static/logo.png"

col1, col2 = st.columns([6, 2])

with col1:
    st.markdown(f"""
    <div class="dashboard-header">
        <div class="header-main-text">
            <h1>Convert PDF invoices to Excel instantly</h1>
            <img src="{logo_url}" class="header-logo" alt="Hawelha Telecom Logo">
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="display:flex; justify-content:flex-end; align-items:center; gap:15px; padding-top:10px;">
        <div class="header-user-info">
            <div class="user-avatar">{user_initial}</div>
            <span class="user-name">مرحباً، {st.session_state.username}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("") 

    if st.button("🚪 تسجيل الخروج", key="logout_btn", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.show_admin_panel = False
        st.rerun()

    if st.session_state.get("role") == "admin":
        if st.button("⚙️ Manage app", key="manage_app_btn", use_container_width=True):
            st.session_state.show_admin_panel = True
            st.rerun()

# ================= ADMIN PANEL (Real Management) =================
if st.session_state.get("show_admin_panel", False) and st.session_state.get("role") == "admin":
    st.markdown("---")
    st.markdown("### ⚙️ لوحة إدارة المستخدمين")

    st.markdown("#### قائمة المستخدمين الحاليين:")
    st.dataframe(df_users, use_container_width=True)

    st.markdown("#### ➕ إضافة مستخدم جديد:")
    with st.form("add_user_form"):
        new_username = st.text_input("اسم المستخدم الجديد")
        new_password = st.text_input("كلمة المرور", type="password")
        new_role = st.selectbox("الدور", ["user", "admin"])
        submitted = st.form_submit_button("إضافة المستخدم")

        if submitted:
            if new_username and new_password:
                if new_username in users:
                    st.error("❌ اسم المستخدم موجود بالفعل!")
                else:
                    new_row = pd.DataFrame([{
                        "Username": new_username,
                        "Password": new_password,
                        "Role": new_role
                    }])
                    df_users = pd.concat([df_users, new_row], ignore_index=True)
                    
                    df_users.to_excel("users.xlsx", index=False)
                    
                    users[new_username] = {
                        "password": new_password,
                        "role": new_role
                    }
                    
                    st.success(f"✅ تم إضافة المستخدم '{new_username}' بنجاح!")
                    st.rerun()
            else:
                st.error("❌ يرجى ملء جميع الحقول!")

    if st.button("🔙 العودة للداشبورد", key="close_admin"):
        st.session_state.show_admin_panel = False
        st.rerun()

    st.markdown("---")

# ================= MODE SELECTION =================
mode = st.radio(
    "🌐 وضع التحليل",
    ["Auto 🤖", "عربي 🇪", "English 🌍"],
    horizontal=True,
    label_visibility="collapsed"
)

# =========================================================
# 🚫 DO NOT MODIFY BELOW THIS LINE (Logic Preserved) 🚫
# =========================================================

def normalize(t):
    return (t or "").replace("−","-").replace("–","-").replace("—","-")

def extract_numbers(text):
    if not text:
        return []
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

# ================= AR Parser =================
def parse_ar(file):
    records = []
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages[2:]:
                for table in page.extract_tables() or []:
                    i = 0
                    while i < len(table):
                        row = table[i]
                        if not row:
                            i += 1
                            continue

                        text = normalize(" ".join([str(c) for c in row if c]))
                        phone = re.search(r'(01[0125]\d{8})', text)

                        if phone:
                            phone = phone.group(1)
                            vals = extract_numbers(text)

                            if i+1 < len(table):
                                nxt = extract_numbers(" ".join([str(c) for c in table[i+1] if c]))
                                if len(nxt) > len(vals):
                                    vals = nxt
                                    i += 1

                            vals = clean_numbers(vals, phone)
                            vals = vals[::-1]

                            def g(i): return vals[i] if i < len(vals) else 0

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
                                "رسوم تسويات": g(10),
                                "ضرائب": g(11),
                                "إجمالي": g(12),
                            })
                        i += 1
    except Exception as e:
        st.warning(f"Error parsing AR file: {e}")
    return records

# ================= EN Parser =================
def parse_en(file):
    records = []
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages[2:]:
                for table in page.extract_tables() or []:
                    i = 0
                    while i < len(table):
                        row = table[i]
                        if not row:
                            i += 1
                            continue

                        text = " ".join([str(c) for c in row])
                        phone = re.search(r'(01[0125]\d{8})', text)

                        if phone:
                            phone = phone.group(1)
                            vals = extract_numbers(
                                " ".join([str(c) for c in table[i+1] if c]) if i+1 < len(table) else ""
                            )

                            vals = clean_numbers(vals, phone)

                            records.append({
                                "محمول": phone,
                                "رسوم شهرية": vals[0] if len(vals)>0 else 0,
                                "رسوم الخدمات": vals[1] if len(vals)>1 else 0,
                                "مكالمات محلية": vals[2] if len(vals)>2 else 0,
                                "رسائل محلية": vals[3] if len(vals)>3 else 0,
                                "إنترنت محلية": vals[4] if len(vals)>4 else 0,
                                "مكالمات دولية": vals[5] if len(vals)>5 else 0,
                                "رسائل دولية": vals[6] if len(vals)>6 else 0,
                                "مكالمات تجوال": vals[7] if len(vals)>7 else 0,
                                "رسائل تجوال": vals[8] if len(vals)>8 else 0,
                                "إنترنت تجوال": vals[9] if len(vals)>9 else 0,
                                "رسوم تسويات": vals[10] if len(vals)>10 else 0,
                                "ضرائب": vals[11] if len(vals)>11 else 0,
                                "إجمالي": vals[-1] if vals else 0
                            })

                            i += 2
                            continue

                        i += 1
    except Exception as e:
        st.warning(f"Error parsing EN file: {e}")
    return records

# ================= AI Parser =================
def parse_ai(file):
    records = []
    try:
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                text += normalize(page.extract_text() or "")

        phone_match = re.search(r'(01[0125]\d{8}|\b1[0125]\d{8}\b)', text)
        if not phone_match:
            return []

        phone = fix_phone(phone_match.group(1))

        def get(pattern):
            match = re.search(pattern, text)
            return float(match.group(1)) if match else 0

        monthly = get(r'إجمالي الرسوم الشهرية.*?(\d+\.\d+)')
        tax1 = get(r'ضريبة الجدول.*?(\d+\.\d+)')
        tax2 = get(r'ضريبة القيمة المضافة.*?(\d+\.\d+)')
        tax3 = get(r'ضريبة الدمغة.*?(\d+\.\d+)')
        tax4 = get(r'تنمية موارد الدولة.*?(\d+\.\d+)')

        taxes = tax1 + tax2 + tax3 + tax4
        total = get(r'إجمالي القيمة المستحقة.*?(\d+\.\d+)')

        records.append({
            "محمول": phone,
            "رسوم شهرية": monthly,
            "رسوم الخدمات": 0,
            "مكالمات محلية": 0,
            "رسائل محلية": 0,
            "إنترنت محلية": 0,
            "مكالمات دولية": 0,
            "رسائل دولية": 0,
            "مكالمات تجوال": 0,
            "رسائل تجوال": 0,
            "إنترنت تجوال": 0,
            "رسوم تسويات": 0,
            "ضرائب": round(taxes, 2),
            "إجمالي": total
        })

    except Exception as e:
        st.warning(f"Error parsing AI file: {e}")
        return []

    return records

# ================= EXCEL EXPORT =================
def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    out.seek(0)
    return out

# ================= FILE UPLOAD & PROCESSING =================
files = st.file_uploader("📂 رفع ملفات PDF", type=["pdf"], accept_multiple_files=True)

if files:
    if st.button("🚀 بدء المعالجة والتحليل", use_container_width=True):
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        all_data = []

        for idx, file in enumerate(files):
            status_text.text(f"⏳ جاري معالجة: {file.name}")
            progress_bar.progress((idx+1)/len(files))

            if mode == "English 🌍":
                data = parse_en(file)
            elif mode == "Auto 🤖":
                data = parse_ar(file)
                if not data:
                    data = parse_en(file)
                if not data: 
                    data = parse_ai(file)
            else:
                data = parse_ar(file)
                
            if not data: 
                data = parse_ai(file)

            all_data.extend(data)
            gc.collect()

        progress_bar.progress(100)
        status_text.empty()

        if all_data:
            df_result = pd.DataFrame(all_data)
            
            total_lines = len(df_result)
            sum_monthly = df_result["رسوم شهرية"].sum()
            sum_settlements = df_result["رسوم تسويات"].sum()
            sum_taxes = df_result["ضرائب"].sum()
            sum_total = df_result["إجمالي"].sum()

            def fmt_curr(val):
                return f"{val:,.0f} ج.م"

            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("### 📈 ملخص التحليل المالي")
            
            m1, m2, m3, m4, m5 = st.columns(5)
            
            with m1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📱 إجمالي الخطوط</div>
                    <div class="metric-value">{total_lines}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with m2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">💰 الرسوم الشهرية</div>
                    <div class="metric-value">{fmt_curr(sum_monthly)}</div>
                </div>
                """, unsafe_allow_html=True)

            with m3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🧾 رسوم التسويات</div>
                    <div class="metric-value">{fmt_curr(sum_settlements)}</div>
                </div>
                """, unsafe_allow_html=True)

            with m4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🏛️ إجمالي الضرائب</div>
                    <div class="metric-value">{fmt_curr(sum_taxes)}</div>
                </div>
                """, unsafe_allow_html=True)

            with m5:
                st.markdown(f"""
                <div class="metric-card" style="border-right-color: #004d40;">
                    <div class="metric-title">💎 الإجمالي الكلي</div>
                    <div class="metric-value" style="color:#004d40;">{fmt_curr(sum_total)}</div>
                </div>
                """, unsafe_allow_html=True)

            st.success("✅ تم الانتهاء من معالجة الملفات بنجاح!")
            
            st.markdown("---")
            st.markdown("### 📋 تفاصيل البيانات")
            st.dataframe(df_result, use_container_width=True, hide_index=True)

            st.download_button(
                label="📥 تحميل تقرير Excel",
                data=to_excel(df_result),
                file_name="Hawelha_Telecom_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# ================= FOOTER =================
st.markdown("""
<div class="footer">
    © 2026 Najat El Bakry — All Rights Reserved | Powered by Streamlit
</div>
""", unsafe_allow_html=True)
