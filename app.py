import streamlit as st
import pdfplumber
import pandas as pd
import re
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
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@700;800&family=Tajawal:wght@400;500;700&display=swap');

html, body { font-family: 'Tajawal', sans-serif; background: #f6f8f7; }
h1, h2, h3 { font-family: 'Cairo', sans-serif; font-weight: 800; }

.header {
    background: linear-gradient(135deg, #047857, #10b981);
    padding: 60px 20px;
    border-radius: 20px;
    text-align: center;
    color: white;
}
.header img { width: 520px; }

.upload-box {
    background: white;
    border-radius: 18px;
    padding: 50px;
    text-align: center;
    margin-top: 20px;
}

.stButton>button {
    background: linear-gradient(135deg, #059669, #10b981);
    color: white;
    padding: 14px;
    border-radius: 12px;
}

.kpi {
    background: white;
    border-radius: 16px;
    padding: 22px;
    text-align: center;
    margin-top: 20px;
}
.kpi h2 { font-size: 28px; color: #065f46; }

.success-box {
    background: white;
    border-radius: 22px;
    padding: 60px;
    text-align: center;
    margin-top: 40px;
}
.success-box h1 {
    font-size: 46px;
    color: #064e3b;
}

.footer {
    margin-top: 80px;
    text-align: center;
}
.signature {
    font-size: 22px;
    font-weight: 800;
    background: linear-gradient(90deg, #047857, #10b981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
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
    text = re.sub(r'01[0125]\d{8}', '', text)
    nums = re.findall(r'-?\d+(?:\.\d+)?', text)
    return [float(x) for x in nums]

# ================= PARSE AR =================
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
                    phone_match = re.search(r'(01[0125]\d{8})', text)

                    if phone_match:
                        phone = phone_match.group(1)
                        values = extract_numbers(text)

                        if i+1 < len(table):
                            next_row = " ".join([str(c) for c in table[i+1] if c])
                            next_vals = extract_numbers(next_row)
                            if len(next_vals) > len(values):
                                values = next_vals
                                i += 1

                        values = values[::-1]

                        def g(i): return values[i] if i < len(values) else 0

                        records.append({
                            "المصدر": file.name,  # 🔥 جديد
                            "محمول": str(phone),
                            "رسوم شهرية": g(0),
                            "رسوم الخدمات": g(1),
                            "إجمالي": g(12),
                        })

                    i += 1
    return records

# ================= PARSE EN =================
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
                    phone_match = re.search(r'(01[0125]\d{8})', text)

                    if phone_match:
                        phone = phone_match.group(1)

                        values = []
                        if i+1 < len(table):
                            next_row = " ".join([str(c) for c in table[i+1] if c])
                            values = extract_numbers(next_row)

                        records.append({
                            "المصدر": file.name,  # 🔥 جديد
                            "محمول": str(phone),
                            "رسوم شهرية": values[0] if len(values)>0 else 0,
                            "رسوم الخدمات": values[1] if len(values)>1 else 0,
                            "إجمالي": values[-1] if values else 0
                        })

                        i += 2
                        continue

                    i += 1
    return records

# ================= MAIN =================
st.markdown('<div class="upload-box"><h2>📁 ارفع ملفات PDF (يمكنك رفع أكثر من ملف)</h2></div>', unsafe_allow_html=True)

files = st.file_uploader("", type=["pdf"], accept_multiple_files=True)

if files:
    if st.button("🚀 بدء التحويل لكل الملفات"):

        all_data = []

        for file in files:

            if mode == "Auto 🤖":
                with pdfplumber.open(file) as pdf:
                    text = pdf.pages[0].extract_text() or ""
                lang = "ar" if re.search(r'[\u0600-\u06FF]', text) else "en"
            else:
                lang = "ar" if mode == "عربي 🇪🇬" else "en"

            data = parse_ar(file) if lang == "ar" else parse_en(file)
            all_data.extend(data)

        if all_data:
            df = pd.DataFrame(all_data)

            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="kpi"><h2>{len(df)}</h2><p>عدد السجلات</p></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="kpi"><h2>{df["رسوم شهرية"].sum():.0f}</h2><p>إجمالي الرسوم الشهرية</p></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="kpi"><h2>{df["إجمالي"].sum():.0f}</h2><p>الإجمالي</p></div>', unsafe_allow_html=True)

            st.dataframe(df.head(20), use_container_width=True)

            output = io.BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            st.markdown("""
            <div class="success-box">
                <h1>🎉 تم تحويل كل الملفات بنجاح</h1>
                <p>ملف Excel واحد يحتوي على كل البيانات</p>
            </div>
            """, unsafe_allow_html=True)

            st.download_button("📥 تحميل ملف Excel الموحد", output, "hawelha_all_files.xlsx")

# ================= FOOTER =================
st.markdown("""
<div class="footer">
    <div>Hawelha Telecom</div>
    <div class="signature">Built by Najat El Bakry</div>
    <div>© 2026 All Rights Reserved</div>
</div>
""", unsafe_allow_html=True)
