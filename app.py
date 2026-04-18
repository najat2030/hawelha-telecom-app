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
PRIMARY_COLOR = "#0B6B3A"  # Royal Green
BG_COLOR = "#F4F6F8"
CARD_BG = "#FFFFFF"

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

    .login-background {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: #F4F6F8;
        z-index: -1;
    }

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

    /* ===== Header ===== */
    .dashboard-header {
        background: white;
        padding: 20px 24px;
        border-radius: 0 0 22px 22px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.05);
        margin-bottom: 26px;
        border-bottom: 4px solid #0B6B3A;
        min-height: 230px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .header-logo-wrap {
        text-align: center;
        width: 100%;
    }

    .header-logo {
        width: 520px;
        max-width: 90%;
        height: auto;
        display: block;
        object-fit: contain;
        margin: 0 auto;
    }

    /* ===== Royal Green Header Boxes ===== */
    .royal-green-box {
        background-color: #1a7e43 !important;
        color: white !important;
        padding: 10px 20px !important;
        border-radius: 50px !important;
        border: 2px solid #146435 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 600 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        transition: all 0.3s ease;
        margin: 0 !important;
        min-height: 55px !important;
        width: 100%;
        box-sizing: border-box;
        direction: rtl;
        gap: 12px;
    }

    .avatar-circle-white {
        background-color: white !important;
        color: #1a7e43 !important;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        flex-shrink: 0;
    }

    .user-name-royal {
        color: white;
        font-size: 16px;
        font-weight: 700;
        white-space: nowrap;
    }

    .logout-marker, .process-marker {
        height: 0;
        margin: 0;
        padding: 0;
    }

    /* ===== Buttons ===== */
    div.stButton > button {
        border-radius: 50px !important;
        font-weight: 700 !important;
        min-height: 55px !important;
        transition: all 0.3s ease !important;
    }

    /* Logout button => Royal Green */
    .logout-marker + div.stButton > button {
        background-color: #1a7e43 !important;
        color: white !important;
        border: 2px solid #146435 !important;
        box-shadow: none !important;
        width: 100% !important;
        font-size: 16px !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        font-weight: 600 !important;
    }

    .logout-marker + div.stButton > button:hover {
        background-color: #146435 !important;
        color: white !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
        transform: translateY(-2px) !important;
    }

    /* Manage app keeps default-ish style */
    div.stButton > button[kind="secondary"] {
        border-radius: 14px !important;
    }

    /* Process button royal green */
    .process-marker + div.stButton > button {
        background-color: #1a7e43 !important;
        color: white !important;
        width: 100% !important;
        border-radius: 12px !important;
        padding: 15px !important;
        font-weight: 800 !important;
        border: none !important;
        font-size: 18px !important;
        box-shadow: 0 8px 20px rgba(26,126,67,0.18) !important;
    }

    .process-marker + div.stButton > button:hover {
        background-color: #146435 !important;
        color: white !important;
    }

    /* File uploader dashed area */
    .stFileUploader section {
        border: 2px dashed #cccccc !important;
        border-radius: 12px !important;
        background-color: #ffffff !important;
    }

    /* Gold progress bar */
    .stProgress > div > div > div > div {
        background-color: #daa520 !important;
    }

    .processing-box {
        background: #ffffff;
        color: #666;
        padding: 12px 18px;
        border-radius: 14px;
        font-weight: 700;
        text-align: right;
        box-shadow: 0 4px 14px rgba(0,0,0,0.05);
        border: 1px solid #ececec;
        margin-top: 10px;
        margin-bottom: 10px;
        direction: rtl;
    }

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

# ================= LOGGING =================
LOG_FILE = "activity_log.csv"

def log_action(user, action, details=""):
    try:
        log_row = pd.DataFrame([{
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user if user else "Unknown",
            "action": action,
            "details": details
        }])

        if os.path.exists(LOG_FILE):
            old_logs = pd.read_csv(LOG_FILE)
            all_logs = pd.concat([old_logs, log_row], ignore_index=True)
            all_logs.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
        else:
            log_row.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
    except Exception:
        pass

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

        if st.button("تسجيل الدخول", width="stretch"):
            if username in users and users[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = users[username]["role"]
                st.session_state.show_admin_panel = False
                log_action(username, "Login Success", "Logged in successfully")
                st.rerun()
            else:
                log_action(username, "Login Failed", "Wrong username or password")
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

top_left, top_center, top_right = st.columns([1, 2, 1], vertical_alignment="center")

with top_left:
    st.markdown('<div class="logout-marker"></div>', unsafe_allow_html=True)
    if st.button("🚪 تسجيل الخروج", key="logout_btn", width="stretch"):
        log_action(st.session_state.username, "Logout", "User logged out")
        st.session_state.logged_in = False
        st.session_state.show_admin_panel = False
        st.rerun()

with top_center:
    st.markdown(f"""
    <div class="dashboard-header">
        <div class="header-logo-wrap">
            <img src="{logo_url}" class="header-logo" alt="Hawelha Telecom Logo">
        </div>
    </div>
    """, unsafe_allow_html=True)

with top_right:
    st.markdown(f"""
    <div class="royal-green-box">
        <div class="avatar-circle-white">{user_initial}</div>
        <span class="user-name-royal">مرحباً، {st.session_state.username}</span>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.get("role") == "admin":
    if st.button("⚙️ Manage app", key="manage_app_btn", width="stretch"):
        log_action(st.session_state.username, "Open Admin Panel", "Admin panel opened")
        st.session_state.show_admin_panel = True
        st.rerun()

# ================= ADMIN PANEL (Real Management) =================
if st.session_state.get("show_admin_panel", False) and st.session_state.get("role") == "admin":
    st.markdown("---")
    st.markdown("### ⚙️ لوحة إدارة المستخدمين")

    st.markdown("#### قائمة المستخدمين الحاليين:")
    st.dataframe(df_users, width="stretch")

    st.markdown("#### ➕ إضافة مستخدم جديد:")
    with st.form("add_user_form"):
        new_username = st.text_input("اسم المستخدم الجديد")
        new_password = st.text_input("كلمة المرور", type="password")
        new_role = st.selectbox("الدور", ["user", "admin"])
        submitted = st.form_submit_button("إضافة المستخدم")

        if submitted:
            if new_username and new_password:
                if new_username in users:
                    log_action(st.session_state.username, "Add User Failed", f"Username already exists: {new_username}")
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

                    log_action(st.session_state.username, "User Added", f"Added user: {new_username} | Role: {new_role}")
                    st.success(f"✅ تم إضافة المستخدم '{new_username}' بنجاح!")
                    st.rerun()
            else:
                log_action(st.session_state.username, "Add User Failed", "Missing required fields")
                st.error("❌ يرجى ملء جميع الحقول!")

    if st.button("🔙 العودة للداشبورد", key="close_admin"):
        log_action(st.session_state.username, "Close Admin Panel", "Returned to dashboard")
        st.session_state.show_admin_panel = False
        st.rerun()

    st.markdown("---")

    # ===== Logs Viewer for Admin =====
    st.markdown("### 📋 سجل الاستخدام")
    if os.path.exists(LOG_FILE):
        try:
            logs_df = pd.read_csv(LOG_FILE)
            st.dataframe(logs_df, width="stretch", hide_index=True)

            log_csv = logs_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📥 تحميل سجل الاستخدام",
                data=log_csv,
                file_name="activity_log.csv",
                mime="text/csv"
            )
        except Exception:
            st.warning("تعذر قراءة ملف السجل.")
    else:
        st.info("لا يوجد سجل استخدام حتى الآن.")

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
    return (t or "").replace("−", "-").replace("–", "-").replace("—", "-")

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

                            if i + 1 < len(table):
                                nxt = extract_numbers(" ".join([str(c) for c in table[i + 1] if c]))
                                if len(nxt) > len(vals):
                                    vals = nxt
                                    i += 1

                            vals = clean_numbers(vals, phone)
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
    except Exception as e:
        st.warning(f"Error parsing AR file: {e}")
        log_action(st.session_state.get("username", "Unknown"), "Parse AR Error", str(e))
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
                                " ".join([str(c) for c in table[i + 1] if c]) if i + 1 < len(table) else ""
                            )

                            vals = clean_numbers(vals, phone)

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
    except Exception as e:
        st.warning(f"Error parsing EN file: {e}")
        log_action(st.session_state.get("username", "Unknown"), "Parse EN Error", str(e))
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
        log_action(st.session_state.get("username", "Unknown"), "Parse AI Error", str(e))
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

st.markdown('<div class="process-marker"></div>', unsafe_allow_html=True)
if st.button("🚀 بدء المعالجة والتحليل", key="process_btn", width="stretch"):
    log_action(st.session_state.username, "Processing Started", f"Files count: {len(files) if files else 0} | Mode: {mode}")

    if files:
        progress_bar = st.progress(0)
        status_text = st.empty()
        all_data = []

        for idx, file in enumerate(files):
            status_text.markdown(
                f'<div class="processing-box">... جاري المعالجة {file.name}</div>',
                unsafe_allow_html=True
            )
            progress_bar.progress((idx + 1) / len(files))
            log_action(st.session_state.username, "Processing File", file.name)

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
            log_action(st.session_state.username, "Processing Completed", f"Total lines extracted: {total_lines}")

            st.markdown("---")
            st.markdown("### 📋 تفاصيل البيانات")
            st.dataframe(df_result, width="stretch", hide_index=True)

            st.download_button(
                label="📥 تحميل تقرير Excel",
                data=to_excel(df_result),
                file_name="Hawelha_Telecom_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            log_action(st.session_state.username, "Processing Completed", "No data extracted from uploaded files")
            st.warning("لم يتم استخراج بيانات من الملفات المرفوعة.")
    else:
        st.warning("⚠️ يرجى رفع ملف PDF واحد على الأقل قبل بدء المعالجة.")

# ================= FOOTER =================
st.markdown("""
<div class="footer">
    © 2026 Najat El Bakry — All Rights Reserved | Powered by Streamlit
</div>
""", unsafe_allow_html=True)
