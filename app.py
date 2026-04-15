import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os

# ================= CONFIG =================
st.set_page_config(page_title="Hawelha Telecom", layout="wide")

# ================= SIMPLE AUTH =================
if "login" not in st.session_state:
    st.session_state.login = False

def login_page():
    st.markdown("<h1 style='text-align:center'>Hawelha Telecom</h1>", unsafe_allow_html=True)
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == "admin" and pw == "1234":
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Wrong credentials")

# ================= LANDING =================
def landing():
    st.markdown("""
    <div style="text-align:center;padding:80px">
        <h1 style="font-size:50px;">حوّلها تليكوم</h1>
        <p style="font-size:20px;color:gray">
        تحويل فواتير PDF إلى Excel بضغطة زر
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Start Now"):
        st.session_state.page = "app"
        st.rerun()

# ================= HELPERS =================
def normalize(t):
    return (t or "").replace("−","-").replace("–","-")

def extract_numbers(text):
    text = normalize(text)
    text = re.sub(r'01[0125]\d{8}', '', text)
    nums = re.findall(r'-?\d+(?:\.\d+)?', text)
    return [float(x) for x in nums]

# ================= PARSE =================
def parse(file):
    records = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages[2:]:
            for table in page.extract_tables() or []:
                for row in table:
                    if not row:
                        continue
                    text = " ".join([str(c) for c in row if c])
                    phone_match = re.search(r'(01[0125]\d{8})', text)
                    if phone_match:
                        phone = phone_match.group(1)
                        values = extract_numbers(text)

                        records.append({
                            "محمول": str(phone),
                            "رسوم شهرية": values[0] if len(values)>0 else 0,
                            "إجمالي": values[-1] if values else 0
                        })
    return records

# ================= APP =================
def app():

    st.markdown("## 📊 Dashboard")

    files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)

    if files:
        all_data = []

        for f in files:
            data = parse(f)
            all_data.extend(data)

        if all_data:
            df = pd.DataFrame(all_data)

            c1, c2, c3 = st.columns(3)
            c1.metric("عدد الخطوط", len(df))
            c2.metric("إجمالي الرسوم", int(df["رسوم شهرية"].sum()))
            c3.metric("الإجمالي", int(df["إجمالي"].sum()))

            st.dataframe(df, use_container_width=True)

            output = io.BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            st.download_button("📥 Download Excel", output, "hawelha.xlsx")

            st.success("✔ تم تحويل كل الملفات بنجاح")

# ================= ROUTER =================
if not st.session_state.login:
    login_page()
else:
    if "page" not in st.session_state:
        st.session_state.page = "landing"

    if st.session_state.page == "landing":
        landing()
    else:
        app()
