import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
import gc

# ================= CONFIG =================
st.set_page_config(
    page_title="Nagat Telecom",
    layout="wide"
)

# ================= STYLE =================
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp {
    background-color: #F8F9FA;
}

.block-container {
    padding-top: 2rem;
}

h1, h2, h3 {
    color: #0B6B3A;
}

div.stButton > button {
    background-color: #1F8A5F;
    color: white;
    border-radius: 10px;
    padding: 10px 25px;
}

div.stButton > button:hover {
    background-color: #166644;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0px 2px 10px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# ================= USERS =================
df_users = pd.read_excel("users.xlsx")

users = {
    row["Username"]: {
        "password": str(row["Password"]),
        "role": row["Role"]
    }
    for _, row in df_users.iterrows()
}

# ================= LOGIN =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.markdown("<h2 style='text-align:center;color:#0B6B3A;'>🔐 تسجيل الدخول</h2>", unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("دخول"):
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]
            st.rerun()
        else:
            st.error("بيانات غير صحيحة")

if not st.session_state.logged_in:
    login()
    st.stop()

# ================= SIDEBAR =================
st.sidebar.markdown(f"👤 {st.session_state.username}")

if st.sidebar.button("تسجيل خروج"):
    st.session_state.logged_in = False
    st.rerun()

# ================= LOGO =================
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
        <img src="data:image/png;base64,{logo}" width="60%">
    </div>
    """, unsafe_allow_html=True)

# ================= HEADER TEXT =================
st.markdown("""
<div style='text-align: center; margin-top: 10px;'>
<h3 style='color:#0B6B3A;'>
Convert PDF invoices to Excel instantly ⚡
</h3>
<p style='color: gray; font-size:14px;'>
Simple • Fast • Accurate
</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# ================= ADMIN PANEL =================
if st.session_state.role == "admin":
    st.markdown("### ⚙️ لوحة الإدارة")

    total_users = len(df_users)
    admins = len(df_users[df_users["Role"] == "admin"])
    users_count = len(df_users[df_users["Role"] == "user"])

    c1, c2, c3 = st.columns(3)

    c1.metric("👥 المستخدمين", total_users)
    c2.metric("👑 Admin", admins)
    c3.metric("👤 Users", users_count)

    st.dataframe(df_users, use_container_width=True)

    st.markdown("<br><hr><br>", unsafe_allow_html=True)

# ================= MODE =================
mode = st.radio(
    "🌐 اختر وضع التحليل",
    ["Auto 🤖", "عربي 🇪🇬", "English 🌍"],
    horizontal=True
)

# =========================================================
# 🚫🚫 DO NOT MODIFY BELOW THIS LINE 🚫
# =========================================================

# (اللوجيك كله زي ما هو 👇 بدون أي تغيير)

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

# (باقي الكود زي ما هو بدون لمس...)

# ================= UI =================
files = st.file_uploader(
    "Upload PDF Files",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

# ================= MAIN =================
if files:

    if st.button("🚀 Start Processing"):

        progress_bar = st.progress(0)
        status_text = st.empty()

        all_data = []
        failed_files = []

        total_files = len(files)

        for idx, file in enumerate(files):

            try:
                status_text.markdown(
                    f"<span style='color:#0B6B3A;'>📄 Processing: {file.name}</span>",
                    unsafe_allow_html=True
                )

                progress_bar.progress(int((idx / total_files) * 100))

                if mode == "Auto 🤖":
                    with pdfplumber.open(file) as pdf:
                        text = pdf.pages[0].extract_text() or ""
                    lang = "ar" if re.search(r'[\u0600-\u06FF]', text) else "en"
                else:
                    lang = "ar" if mode == "عربي 🇪🇬" else "en"

                data = []

                try:
                    data = parse_ar(file) if lang == "ar" else parse_en(file)
                except:
                    data = []

                if not data:
                    data = parse_ai(file)

                if data:
                    all_data.extend(data)

            except:
                failed_files.append(file.name)
                continue

            gc.collect()

        progress_bar.progress(100)
        status_text.markdown(
            "<span style='color:green;'>✅ Completed Successfully</span>",
            unsafe_allow_html=True
        )

        if all_data:

            df = pd.DataFrame(all_data)

            total_lines = len(df)
            total_monthly = df["رسوم شهرية"].sum()
            total_settlements = df["رسوم تسويات"].sum()
            total_grand = df["إجمالي"].sum()

            st.markdown("## 📊 Dashboard")

            k1, k2, k3, k4 = st.columns(4)

            k1.metric("عدد الخطوط", total_lines)
            k2.metric("إجمالي الرسوم الشهرية", f"{total_monthly:,.2f}")
            k3.metric("إجمالي التسويات", f"{total_settlements:,.2f}")
            k4.metric("الإجمالي النهائي", f"{total_grand:,.2f}")

            st.dataframe(df.head(20), use_container_width=True)

            excel = to_excel(df)

            st.success("🎉 تم التحويل بنجاح")
            st.download_button("📥 تحميل Excel", excel, "hawelha_all_files.xlsx")

            if failed_files:
                st.warning(f"⚠️ فواتير فشلت: {len(failed_files)}")
                st.write(failed_files)

        else:
            st.error("No data extracted")

# ================= FOOTER =================
st.markdown("""
<hr>
<div style='text-align: center; color: gray; font-size: 13px;'>
© 2026 Najat El Bakry — All Rights Reserved
</div>
""", unsafe_allow_html=True)
