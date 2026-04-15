import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
import base64
import os

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Hawelha Telecom | حوّلها تليكوم",
    page_icon="📊",
    layout="wide"
)

# ================= MODE =================
mode = st.radio(
    "🌐 اختر نوع الملف",
    ["Auto 🤖", "عربي 🇪🇬", "English 🌍"],
    horizontal=True
)

# ================= LOGO =================
def load_logo():
    logo_path = 'static/logo.png'
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

# ================= CORPORATE UI =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body {
    background-color: #0a0f1c;
    font-family: 'Inter', sans-serif;
}

/* HEADER */
.main-header {
    background: linear-gradient(135deg, #020617, #0f172a);
    border: 1px solid #1e293b;
    padding: 30px;
    border-radius: 16px;
    text-align: center;
    margin-bottom: 25px;
}

.main-header img {
    width: 280px;
    max-width: 90%;
    margin-bottom: 15px;
}

/* UPLOAD */
.upload-box {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 40px;
    text-align: center;
    color: white;
}

/* BUTTON */
.stButton>button {
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white;
    font-weight: 600;
    border-radius: 10px;
    padding: 12px;
    border: none;
    width: 100%;
}

/* DASHBOARD CARDS */
.kpi-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 20px;
    text-align: center;
}

.kpi-title {
    color: #94a3b8;
    font-size: 14px;
}

.kpi-value {
    font-size: 26px;
    font-weight: 700;
    color: #38bdf8;
}

/* TABLE */
.dataframe {
    border-radius: 12px;
    overflow: hidden;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background-color: #050b18;
}
</style>
""", unsafe_allow_html=True)

# ================= LOGO =================
logo_data = load_logo()

if logo_data:
    st.markdown(f"""
    <div class="main-header">
        <img src="data:image/png;base64,{logo_data}">
        <h2 style="color:#e2e8f0;">Hawelha Telecom</h2>
        <p style="color:#94a3b8;">Enterprise Billing Automation System</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="main-header">
        <h2 style="color:white;">Hawelha Telecom</h2>
    </div>
    """, unsafe_allow_html=True)

# ================= NORMALIZATION =================
def normalize_text(text):
    if not text:
        return ""
    text = text.replace("−", "-")
    text = text.replace("–", "-")
    return text

# ================= AUTO DETECT =================
def detect_language(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages[:2]:
            text = page.extract_text()
            if text and re.search(r'[\u0600-\u06FF]', text):
                return "ar"
    return "en"

# ================= NUMBER EXTRACTION =================
def extract_numbers(text):
    text = normalize_text(text)
    numbers = re.findall(r'-?\d+(?:\.\d+)?', text)

    values = []
    for n in numbers:
        try:
            values.append(float(n))
        except:
            pass
    return values

# ================= ARABIC ENGINE =================
def extract_ar(uploaded_file):
    records = []

    with pdfplumber.open(uploaded_file) as pdf:
        for page_num in range(2, len(pdf.pages)):
            page = pdf.pages[page_num]
            tables = page.extract_tables()

            for table in tables or []:
                i = 0
                while i < len(table):
                    row = table[i]
                    if not row:
                        i += 1
                        continue

                    row_text = normalize_text(' '.join([str(c) for c in row if c]))
                    phone_match = re.search(r'(01[0125]\d{8})', row_text)

                    if phone_match:
                        phone = phone_match.group(1)

                        values = extract_numbers(row_text)

                        if i + 1 < len(table):
                            next_vals = extract_numbers(' '.join([str(c) for c in table[i+1] if c]))
                            if len(next_vals) > len(values):
                                values = next_vals
                                i += 1

                        values = values[::-1]

                        def g(i):
                            return values[i] if i < len(values) else 0

                        records.append({
                            'محمول': phone,
                            'رسوم شهرية': g(0),
                            'رسوم الخدمات': g(1),
                            'مكالمات محلية': g(2),
                            'رسائل محلية': g(3),
                            'إنترنت محلية': g(4),
                            'مكالمات دولية': g(5),
                            'رسائل دولية': g(6),
                            'مكالمات تجوال': g(7),
                            'رسائل تجوال': g(8),
                            'إنترنت تجوال': g(9),
                            'رسوم وتسويات اخري': g(10),
                            'قيمة الضرائب': g(11),
                            'إجمالي': g(12)
                        })

                    i += 1

    return records

# ================= ENGLISH ENGINE =================
def extract_en(uploaded_file):
    records = []

    with pdfplumber.open(uploaded_file) as pdf:
        for page_num in range(2, len(pdf.pages)):
            page = pdf.pages[page_num]
            tables = page.extract_tables()

            for table in tables or []:
                i = 0
                while i < len(table):
                    row = table[i]
                    if not row:
                        i += 1
                        continue

                    row_text = ' '.join([str(c) for c in row])

                    phone_match = re.search(r'(01[0125]\d{8})', row_text)

                    if phone_match:
                        phone = phone_match.group(1)

                        values = extract_numbers(
                            ' '.join([str(c) for c in table[i+1] if c]) if i+1 < len(table) else ""
                        )

                        records.append({
                            'محمول': phone,
                            'رسوم شهرية': values[0] if len(values)>0 else 0,
                            'رسوم الخدمات': values[1] if len(values)>1 else 0,
                            'مكالمات محلية': values[2] if len(values)>2 else 0,
                            'رسائل محلية': values[3] if len(values)>3 else 0,
                            'إنترنت محلية': values[4] if len(values)>4 else 0,
                            'مكالمات دولية': values[5] if len(values)>5 else 0,
                            'رسائل دولية': values[6] if len(values)>6 else 0,
                            'مكالمات تجوال': values[7] if len(values)>7 else 0,
                            'رسائل تجوال': values[8] if len(values)>8 else 0,
                            'إنترنت تجوال': values[9] if len(values)>9 else 0,
                            'رسوم وتسويات اخري': values[10] if len(values)>10 else 0,
                            'قيمة الضرائب': values[11] if len(values)>11 else 0,
                            'إجمالي': values[12] if len(values)>12 else (values[-1] if values else 0)
                        })

                        i += 2
                        continue

                    i += 1

    return records

# ================= EXCEL =================
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

# ================= MAIN =================
st.markdown("""
<div class="upload-box">
    <h2>📁 Upload PDF Invoice</h2>
    <p>Enterprise-grade PDF Processing System</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["pdf"])

if uploaded_file:

    if st.button("🚀 Process File"):

        with st.spinner("Processing..."):

            if mode == "Auto 🤖":
                lang = detect_language(uploaded_file)
            elif mode == "عربي 🇪🇬":
                lang = "ar"
            else:
                lang = "en"

            records = extract_ar(uploaded_file) if lang == "ar" else extract_en(uploaded_file)

            if records:

                df = pd.DataFrame(records)

                # ================= KPIs =================
                total_lines = len(df)
                total_monthly = df["رسوم شهرية"].sum()
                total_settlement = df["رسوم تسويات اخري"].sum() if "رسوم تسويات اخري" in df else 0
                total_final = df["إجمالي"].sum()

                st.markdown("## 📊 Dashboard Overview")

                col1, col2, col3, col4 = st.columns(4)

                col1.metric("Total Lines", total_lines)
                col2.metric("Monthly Fees", f"{total_monthly:,.2f}")
                col3.metric("Settlements", f"{total_settlement:,.2f}")
                col4.metric("Total Amount", f"{total_final:,.2f}")

                st.dataframe(df.head(10))

                excel = convert_df_to_excel(df)

                st.download_button(
                    "📥 Download Excel",
                    excel,
                    file_name="hawelha_telecom.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            else:
                st.error("No data found")
