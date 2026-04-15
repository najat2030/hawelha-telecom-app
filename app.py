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

# ================= LOGO (UNCHANGED) =================
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

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0b1220;
}

/* MAIN CONTAINER */
.block-container {
    padding: 2rem 3rem;
}

/* HEADER */
.main-header {
    background: linear-gradient(135deg, #0f172a 0%, #111c33 100%);
    border: 1px solid #1f2a44;
    padding: 2rem;
    border-radius: 16px;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

.main-header img {
    max-height: 120px;
    margin-bottom: 1rem;
}

.main-header p {
    color: #94a3b8;
}

/* UPLOAD BOX */
.upload-box {
    background: rgba(255,255,255,0.03);
    border: 1px solid #1f2a44;
    border-radius: 16px;
    padding: 3rem;
    text-align: center;
    transition: 0.3s;
}

.upload-box:hover {
    border-color: #3b82f6;
    transform: translateY(-2px);
}

.upload-box h2 {
    color: #e2e8f0;
}

/* BUTTON */
.stButton>button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 10px;
    font-weight: 600;
    width: 100%;
    box-shadow: 0 4px 15px rgba(37,99,235,0.3);
    transition: 0.3s;
}

.stButton>button:hover {
    transform: translateY(-1px);
}

/* STATS */
.stats-card {
    background: linear-gradient(135deg, #111c33, #0f172a);
    border: 1px solid #1f2a44;
    border-radius: 14px;
    padding: 1.5rem;
    text-align: center;
}

.stats-card h3 {
    color: #60a5fa;
    font-size: 2rem;
    margin: 0;
}

.stats-card p {
    color: #94a3b8;
    font-size: 0.85rem;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background-color: #0a0f1c;
    border-right: 1px solid #1f2a44;
}

section[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
</style>
""", unsafe_allow_html=True)

# ================= LOGO DISPLAY =================
logo_data = load_logo()

if logo_data:
    st.markdown(f"""
    <div class="main-header">
        <img src="data:image/png;base64,{logo_data}" width="220">
        <h2 style="color:#e2e8f0;">Hawelha Telecom</h2>
        <p>Enterprise Data Processing System</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="main-header">
        <h1>Hawelha Telecom</h1>
    </div>
    """, unsafe_allow_html=True)

# ================= TEXT NORMALIZATION =================
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
def extract_etisalat_data_ar(uploaded_file):
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
def extract_etisalat_data_en(uploaded_file):
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

# ================= EXCEL EXPORT =================
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

# ================= MAIN UI =================
st.markdown("""
<div class="upload-box">
    <h2>📁 Upload PDF Invoice</h2>
    <p>Enterprise-grade PDF to Excel Processing System</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["pdf"])

if uploaded_file:

    st.success(f"Uploaded: {uploaded_file.name}")

    if st.button("🚀 Process File"):

        with st.spinner("Processing..."):

            if mode == "Auto 🤖":
                lang = detect_language(uploaded_file)
            elif mode == "عربي 🇪🇬":
                lang = "ar"
            else:
                lang = "en"

            if lang == "ar":
                records = extract_etisalat_data_ar(uploaded_file)
            else:
                records = extract_etisalat_data_en(uploaded_file)

            if records:

                df = pd.DataFrame(records)

                st.success(f"Extracted {len(df)} records")

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
