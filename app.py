import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import os
import gc
import base64
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(
    page_title="Hawelha Telecom | حوّلها تليكوم",
    page_icon="📊",
    layout="wide"
)

# ================= STYLE & THEME =================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

    .stApp {
        background-color: #f8f9fa;
        font-family: 'Tajawal', sans-serif;
    }

    html, body {
        font-family: 'Cairo', sans-serif;
        background: #f8fafc;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    .login-background {
        position: fixed;
        inset: 0;
        background-color: #F4F6F8;
        z-index: -1;
    }

    .login-card {
        background: rgba(255, 255, 255, 0.97);
        padding: 35px 30px;
        border-radius: 20px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.08);
        border: 1px solid rgba(255, 255, 255, 0.4);
        max-width: 430px;
        margin: 70px auto 20px auto;
        text-align: center;
    }

    .login-title {
        color: #1a7e43;
        font-size: 26px;
        font-weight: 800;
        margin-bottom: 20px;
    }

    .login-subtitle {
        color: #666;
        font-size: 14px;
        margin-bottom: 20px;
    }

    /* ===== الأزرار الملكية الأساسية ===== */
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

    .royal-green-box {
        min-height: 45px !important;
        max-height: 45px !important;
        width: fit-content !important;
        padding: 5px 16px !important;
        font-size: 14px !important;
        gap: 8px !important;
        white-space: nowrap !important;
        margin-left: auto !important;
    }

    div.stButton > button {
        min-height: 45px !important;
        max-height: 45px !important;
        width: 100% !important;
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
        margin-left: 8px;
    }

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
    }

    .upload-box {
        background: white;
        border: 2px dashed #10b981;
        border-radius: 16px;
        padding: 25px;
        text-align: center;
        margin-bottom: 10px;
    }

    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-right: 5px solid #1a7e43;
        margin-bottom: 10px;
        text-align: center;
    }

    .metric-title {
        font-size: 18px !important;
        color: #555;
        font-weight: 600 !important;
    }

    .metric-value {
        font-size: 32px !important;
        color: #1a7e43;
        font-weight: 800 !important;
    }

    .process-btn-area + div.stButton > button {
        background: linear-gradient(135deg, #059669, #10b981) !important;
        color: white !important;
        border: none !important;
        min-height: 50px !important;
    }

    .stProgress > div > div > div > div {
        background-color: #daa520 !important;
    }

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

# ================= HELPERS =================
def load_logo():
    path = "static/logo.png"
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo = load_logo()

def normalize(text):
    return (text or "").replace("−", "-").replace("–", "-").replace("—", "-")

# استخراج أرقام يدعم السالب بشكل أفضل
def extract_numbers(text):
    text = normalize(text)
    matches = re.findall(r'(-?\s*\d+(?:\.\d+)?\s*-?)', text)

    numbers = []
    for m in matches:
        m = m.replace(" ", "")
        if m.endswith("-"):
            try:
                val = -float(m[:-1])
                numbers.append(val)
            except:
                pass
        else:
            try:
                val = float(m)
                numbers.append(val)
            except:
                pass

    return numbers

def fix_phone(phone):
    phone = str(phone)
    if len(phone) == 10 and phone.startswith("1"):
        return "0" + phone
    return phone

def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    out.seek(0)
    return out

# ================= USERS DATA =================
def load_users():
    try:
        df_users = pd.read_excel("users.xlsx")
        required_cols = {"Username", "Password"}
        if not required_cols.issubset(df_users.columns):
            st.error("ملف users.xlsx لازم يحتوي على الأعمدة: Username و Password")
            st.stop()

        return {
            str(row["Username"]).strip(): str(row["Password"]).strip()
            for _, row in df_users.iterrows()
        }
    except FileNotFoundError:
        st.error("ملف users.xlsx غير موجود. ارفعيه في نفس مجلد التطبيق.")
        st.stop()
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة users.xlsx: {e}")
        st.stop()

users = load_users()

# ================= SESSION STATE =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# ================= LOGIN PAGE =================
def login_page():
    st.markdown('<div class="login-background"></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown("""
        <div class="login-card">
            <div class="login-title">🔐 تسجيل الدخول</div>
            <div class="login-subtitle">ادخلي اسم المستخدم وكلمة المرور للمتابعة</div>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input(
            "اسم المستخدم",
            placeholder="اسم المستخدم 👤",
            label_visibility="collapsed"
        )
        password = st.text_input(
            "كلمة المرور",
            placeholder="كلمة المرور 🔒",
            type="password",
            label_visibility="collapsed"
        )

        if st.button("تسجيل الدخول", key="login_btn", use_container_width=True):
            username = username.strip()
            password = password.strip()

            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("⚠️ اسم المستخدم أو كلمة المرور غير صحيحة")

# ================= LOGIN CHECK =================
if not st.session_state.logged_in:
    login_page()
    st.stop()

# ================= HEADER =================
logo_url = "https://raw.githubusercontent.com/najat2030/hawelha-telecom-app/main/static/logo.png"

col_out, col_logo, col_me = st.columns([1, 4, 1], vertical_alignment="center")

with col_out:
    if st.button("🚪 تسجيل الخروج", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

with col_logo:
    if logo:
        st.markdown(
            f'<div class="header-container"><img src="data:image/png;base64,{logo}" class="header-logo"></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="header-container"><img src="{logo_url}" class="header-logo"></div>',
            unsafe_allow_html=True
        )

with col_me:
    user_initial = st.session_state.username[0].upper() if st.session_state.username else "?"
    st.markdown(f'''
    <div class="royal-green-box" style="margin-left: auto;">
        <div class="avatar-circle-white">{user_initial}</div>
        <span>مرحباً، {st.session_state.username}</span>
    </div>
    ''', unsafe_allow_html=True)

# ================= MODE =================
mode = st.radio(
    "🌐 اختر وضع التحليل",
    ["Auto 🤖", "عربي 🇪🇬", "English 🌍"],
    horizontal=True
)

# ================= PARSERS =================
def parse_ar(file):
    records = []
    try:
        file.seek(0)
        with pdfplumber.open(file) as pdf:
            total_pages = len(pdf.pages)

            progress = st.progress(0)

            for p, page in enumerate(pdf.pages[2:], start=2):
                if total_pages > 0:
                    progress.progress(min(int((p / total_pages) * 100), 100))

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

                            if i + 1 < len(table):
                                nxt = extract_numbers(" ".join([str(c) for c in table[i + 1] if c]))
                                if len(nxt) > len(vals):
                                    vals = nxt
                                    i += 1

                            vals = vals[::-1]

                            def g(idx):
                                return vals[idx] if idx < len(vals) else 0

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

            progress.empty()
    except Exception:
        return []
    return records

def parse_en(file):
    records = []
    try:
        file.seek(0)
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages[2:]:
                for table in page.extract_tables() or []:
                    i = 0
                    while i < len(table):
                        row = table[i]
                        if not row:
                            i += 1
                            continue

                        text = " ".join([str(c) for c in row if c])
                        phone = re.search(r'(01[0125]\d{8})', text)

                        if phone:
                            phone = phone.group(1)

                            vals = extract_numbers(
                                " ".join([str(c) for c in table[i + 1] if c]) if i + 1 < len(table) else ""
                            )
                            vals = [v for v in vals if str(int(v)) != str(int(phone))]

                            records.append({
                                "محمول": phone,
                                "رسوم شهرية": vals[0] if len(vals) > 0 else 0,
                                "رسوم الخدمات": vals[1] if len(vals) > 1 else 0,
                                "مكالمات محلية": vals[2] if len(vals) > 2 else 0,
                                "رسائل محلية": vals[3] if len(vals) > 3 else 0,
                                "إنترنت محلية": vals[4] if len(vals) > 4 else 0,
                                "مكالمات دولية": vals[5] if len(vals) > 5 else 0,
                                "رسائل دولية": vals[6] if len(vals) > 6 else 0,
                                "مكالمات تجوال": vals[7] if len(vals) > 7 else 0,
                                "رسائل تجوال": vals[8] if len(vals) > 8 else 0,
                                "إنترنت تجوال": vals[9] if len(vals) > 9 else 0,
                                "رسوم تسويات": vals[10] if len(vals) > 10 else 0,
                                "ضرائب": vals[11] if len(vals) > 11 else 0,
                                "إجمالي": vals[-1] if vals else 0
                            })

                            i += 2
                            continue

                        i += 1
    except Exception:
        return []
    return records

def parse_ai(file):
    records = []
    try:
        file.seek(0)
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

    except Exception:
        return []

    return records

# ================= INPUT =================
st.markdown("""
<div class="upload-box">
    <h2>📁 Upload PDF Invoice</h2>
</div>
""", unsafe_allow_html=True)

files = st.file_uploader("", type=["pdf"], accept_multiple_files=True)

# ================= MAIN =================
st.markdown('<div class="process-btn-area"></div>', unsafe_allow_html=True)
if st.button("🚀 Start Processing", key="process_btn"):
    if files:
        with st.spinner("Processing..."):
            progress_bar = st.progress(0)
            all_data = []

            for idx, file in enumerate(files):
                if mode == "English 🌍":
                    file.seek(0)
                    data = parse_en(file)

                elif mode == "عربي 🇪🇬":
                    file.seek(0)
                    data = parse_ar(file)

                else:
                    file.seek(0)
                    data = parse_ar(file)

                    if not data:
                        file.seek(0)
                        data = parse_en(file)

                    if not data:
                        file.seek(0)
                        data = parse_ai(file)

                if not data:
                    file.seek(0)
                    data = parse_ai(file)

                all_data.extend(data)
                progress_bar.progress((idx + 1) / len(files))
                gc.collect()

            progress_bar.empty()

            if all_data:
                df = pd.DataFrame(all_data)

                total_lines = len(df)
                total_monthly = df["رسوم شهرية"].sum()
                total_settlement = df["رسوم تسويات"].sum()
                total_taxes = df["ضرائب"].sum()
                total_total = df["إجمالي"].sum()

                st.markdown("## 📊 Dashboard")

                c1, c2, c3, c4, c5 = st.columns(5)

                c1.markdown(f'<div class="metric-card"><div class="metric-title">📱 إجمالي الخطوط</div><div class="metric-value">{total_lines}</div></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-card"><div class="metric-title">💰 الرسوم الشهرية</div><div class="metric-value">{total_monthly:,.2f}</div></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-card"><div class="metric-title">🧾 رسوم التسويات</div><div class="metric-value">{total_settlement:,.2f}</div></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="metric-card"><div class="metric-title">🏛️ إجمالي الضرائب</div><div class="metric-value">{total_taxes:,.2f}</div></div>', unsafe_allow_html=True)
                c5.markdown(f'<div class="metric-card"><div class="metric-title">💎 الإجمالي</div><div class="metric-value">{total_total:,.2f}</div></div>', unsafe_allow_html=True)

                st.markdown("---")
                st.dataframe(df, use_container_width=True)

                excel = to_excel(df)

                st.success("✅ تم التحويل بنجاح")

                st.download_button(
                    "📥 تحميل Excel",
                    excel,
                    file_name="hawelha.xlsx"
                )

            else:
                st.error("No data found")
    else:
        st.info("يرجى رفع الملفات أولاً.")

# ================= FOOTER =================
st.markdown("""
<div class="footer">
    © 2026 Najat El Bakry — All Rights Reserved | Powered by Streamlit
</div>
""", unsafe_allow_html=True)
