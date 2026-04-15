import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
import zipfile
from datetime import datetime

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
html, body { font-family: 'Cairo', sans-serif; background: #f8fafc; }

.header {
    background: linear-gradient(135deg, #059669, #10b981);
    padding: 40px;
    border-radius: 18px;
    text-align: center;
    color: white;
}
.header img { width: 420px; }

.upload-box {
    background: white;
    border: 2px dashed #10b981;
    border-radius: 16px;
    padding: 40px;
    text-align: center;
}

.stButton>button {
    background: linear-gradient(135deg, #059669, #10b981);
    color: white;
    padding: 12px;
    border-radius: 10px;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
if logo:
    st.markdown(f"""
    <div class="header">
        <img src="data:image/png;base64,{logo}">
        <h1>Hawelha Telecom</h1>
    </div>
    """, unsafe_allow_html=True)

# ================= HELPERS =================
def normalize(t):
    return (t or "").replace("−","-").replace("–","-")

def extract_numbers(text):
    text = normalize(text)
    return [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', text)]

# ================= PARSER =================
def parse_ar(file):
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
                        })
    return records

# ================= EXCEL =================
def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    out.seek(0)
    return out

# ================= INPUT =================
st.markdown("""
<div class="upload-box">
    <h2>📁 ارفع ملفات PDF</h2>
</div>
""", unsafe_allow_html=True)

files = st.file_uploader("", type=["pdf"], accept_multiple_files=True)

# ================= MAIN =================
if files:

    if st.button("🚀 Start Processing"):

        progress = st.progress(0)
        status = st.empty()

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zipf:

            for i, file in enumerate(files):

                status.text(f"Processing {file.name}...")

                data = parse_ar(file)

                if data:
                    df = pd.DataFrame(data)
                    excel = to_excel(df)

                    filename = file.name.replace(".pdf", ".xlsx")
                    zipf.writestr(filename, excel.getvalue())

                progress.progress((i + 1) / len(files))

        zip_buffer.seek(0)

        st.success("🎉 تم تحويل كل الملفات")

        st.download_button(
            "📦 تحميل كل الملفات ZIP",
            zip_buffer,
            file_name=f"hawelha_all_{datetime.now().strftime('%Y%m%d')}.zip",
            mime="application/zip"
        )
