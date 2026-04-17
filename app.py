import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
import gc

# ================= CONFIG =================
st.set_page_config(page_title="Nagat Telecom", layout="wide")

# ================= STYLE =================
st.markdown("""
<style>

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp {
    background-color: #F4F6F8;
}

/* Header */
.header-box {
    display:flex;
    justify-content:space-between;
    align-items:center;
    background:white;
    padding:15px 25px;
    border-radius:12px;
    box-shadow:0px 2px 10px rgba(0,0,0,0.1);
}

/* Cards */
.card {
    background:white;
    padding:20px;
    border-radius:12px;
    box-shadow:0px 2px 8px rgba(0,0,0,0.08);
    margin-bottom:20px;
}

/* Buttons */
div.stButton > button {
    background-color:#0B6B3A;
    color:white;
    border-radius:8px;
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

# ================= HEADER =================
col1, col2 = st.columns([6,2])

with col1:
    st.markdown("<div class='header-box'><b>📊 Dashboard</b></div>", unsafe_allow_html=True)

with col2:
    st.write(f"👤 {st.session_state.username}")
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ================= ADMIN =================
if st.session_state.role == "admin":
    st.markdown("### ⚙️ Admin Panel")

    c1, c2, c3 = st.columns(3)
    c1.metric("Users", len(df_users))
    c2.metric("Admins", len(df_users[df_users["Role"]=="admin"]))
    c3.metric("Users", len(df_users[df_users["Role"]=="user"]))

    st.dataframe(df_users)
    st.markdown("<hr>", unsafe_allow_html=True)

# ================= MODE =================
mode = st.radio(
    "🌐 اختر وضع التحليل",
    ["Auto 🤖", "عربي 🇪🇬", "English 🌍"],
    horizontal=True
)

# =========================================================
# 🚫🚫 DO NOT MODIFY BELOW THIS LINE 🚫
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

# ================= AR =================
def parse_ar(file):
    records = []
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
    return records

# ================= EN =================
def parse_en(file):
    records = []
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
    return records

# ================= AI =================
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

    except:
        return []

    return records

# ================= EXCEL =================
def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    out.seek(0)
    return out

# ================= UI =================
files = st.file_uploader("Upload PDF Files", type=["pdf"], accept_multiple_files=True)

# ================= PROCESS =================
if files:
    if st.button("🚀 Start Processing"):

        progress_bar = st.progress(0)
        status_text = st.empty()

        all_data = []

        for idx, file in enumerate(files):
            status_text.text(f"📄 {file.name}")
            progress_bar.progress((idx+1)/len(files))

            data = parse_ar(file) if mode != "English 🌍" else parse_en(file)
            if not data:
                data = parse_ai(file)

            all_data.extend(data)
            gc.collect()

        progress_bar.progress(100)

        if all_data:
            df = pd.DataFrame(all_data)

            # ================= DASHBOARD =================
            c1, c2, c3, c4 = st.columns(4)

            c1.metric("📱 عدد الخطوط", len(df))
            c2.metric("💰 رسوم شهرية", int(df["رسوم شهرية"].sum()))
            c3.metric("🧾 ضرائب", int(df["ضرائب"].sum()))
            c4.metric("📊 الإجمالي", int(df["إجمالي"].sum()))

            st.success("🎉 تم التحويل بنجاح")

            st.dataframe(df, use_container_width=True)

            st.download_button("📥 تحميل Excel", to_excel(df), "output.xlsx")

# ================= FOOTER =================
st.markdown("""
<hr>
<div style='text-align:center;color:gray;font-size:13px;'>
© 2026 Najat El Bakry — All Rights Reserved
</div>
""", unsafe_allow_html=True)
