import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
import base64
import os

# ================= CONFIG =================
st.set_page_config(
    page_title="Hawelha Telecom | حوّلها تليكوم",
    page_icon="📊",
    layout="wide"
)

# ================= MODE =================
mode = st.radio(
    "🌐 اختر وضع التحليل",
    ["Auto 🤖", "عربي 🇪🇬", "English 🌍"],
    horizontal=True
)

# ================= LOGO =================
def load_logo():
    path = "static/logo.png"
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo = load_logo()

# ================= UI =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

html, body {
    font-family: 'Cairo', sans-serif;
    background: #f8fafc;
}

.header {
    background: linear-gradient(135deg, #059669, #10b981);
    padding: 40px 20px;
    border-radius: 18px;
    text-align: center;
    color: white;
    margin-bottom: 25px;
}

.header img {
    width: 420px;
    max-width: 95%;
    margin-bottom: 15px;
}

.upload-box {
    background: white;
    border: 2px dashed #10b981;
    border-radius: 16px;
    padding: 45px;
    text-align: center;
}

.stButton>button {
    background: linear-gradient(135deg, #059669, #10b981);
    color: white;
    font-size: 16px;
    font-weight: 700;
    padding: 12px;
    border-radius: 10px;
    width: 100%;
}

.kpi {
    background: white;
    border-radius: 14px;
    padding: 18px;
    text-align: center;
}

.success-box {
    background: #ecfdf5;
    border: 2px solid #10b981;
    border-radius: 16px;
    padding: 25px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
if logo:
    st.markdown(f"""
    <div class="header">
        <img src="data:image/png;base64,{logo}">
        <h1>Hawelha Telecom</h1>
        <p>PDF → Excel Automation System</p>
    </div>
    """, unsafe_allow_html=True)

# ================= HELPERS =================
def normalize(t):
    return (t or "").replace("−","-").replace("–","-")

def extract_numbers(text):
    text = normalize(text)
    return [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', text)]

# ================= PARSER =================
def parse_file(file, lang):
    records = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages[2:]:
            for table in page.extract_tables() or []:
                for row in table:
                    if not row:
                        continue

                    text = normalize(" ".join([str(c) for c in row if c]))
                    phone = re.search(r'(01[0125]\d{8})', text)

                    if phone:
                        phone = phone.group(1)
                        vals = extract_numbers(text)[::-1]

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
                            "اسم الملف": file.name
                        })

    return records

# ================= EXCEL =================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

# ================= INPUT =================
st.markdown("""
<div class="upload-box">
    <h2>📁 Upload PDF Files</h2>
    <p>Upload multiple invoices</p>
</div>
""", unsafe_allow_html=True)

files = st.file_uploader("", type=["pdf"], accept_multiple_files=True)

# ================= MAIN =================
if files:
    if st.button("🚀 Start Processing"):
        with st.spinner("Processing all files..."):

            all_data = []

            for file in files:

                if mode == "Auto 🤖":
                    with pdfplumber.open(file) as pdf:
                        text = pdf.pages[0].extract_text() or ""
                    lang = "ar" if re.search(r'[\u0600-\u06FF]', text) else "en"
                else:
                    lang = "ar" if mode == "عربي 🇪🇬" else "en"

                data = parse_file(file, lang)

                if data:
                    all_data.extend(data)

            if all_data:
                df = pd.DataFrame(all_data)

                # KPIs
                c1, c2 = st.columns(2)
                c1.markdown(f'<div class="kpi"><h2>{len(df)}</h2><p>عدد الخطوط</p></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="kpi"><h2>{df["إجمالي"].sum():.2f}</h2><p>الإجمالي</p></div>', unsafe_allow_html=True)

                st.dataframe(df.head(10), use_container_width=True)

                excel = to_excel(df)

                st.markdown("""
                <div class="success-box">
                    🎉 تم تحويل كل الملفات بنجاح!
                </div>
                """, unsafe_allow_html=True)

                st.download_button(
                    "📥 تحميل Excel",
                    excel,
                    file_name="hawelha_all_files.xlsx"
                )

            else:
                st.error("❌ لم يتم استخراج بيانات")
