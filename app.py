import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os

# ================= CONFIG =================
st.set_page_config(
    page_title="Hawelha Telecom",
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
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@700;800&family=Inter:wght@400;500;600&display=swap');

:root {
    --green: #0f9d58;
    --dark: #111827;
    --gray: #6b7280;
    --bg: #f9fafb;
}

html, body {
    font-family: 'Inter', sans-serif;
    background: var(--bg);
}

/* HEADINGS */
h1, h2, h3 {
    font-family: 'Cairo', sans-serif;
    font-weight: 800;
    color: var(--dark);
}

/* HEADER */
.header {
    background: white;
    padding: 30px;
    border-radius: 16px;
    margin-bottom: 25px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid #eee;
}
.header img {
    height: 70px;
}
.header-title {
    font-size: 26px;
}

/* MAIN CARD */
.main-card {
    background: white;
    padding: 40px;
    border-radius: 16px;
    text-align: center;
    border: 1px solid #eee;
    margin-bottom: 25px;
}
.main-card p {
    color: var(--gray);
}

/* BUTTON */
.stButton>button {
    background: var(--green);
    color: white;
    font-weight: 600;
    padding: 14px;
    border-radius: 10px;
}

/* KPI */
.kpi {
    background: white;
    border-radius: 14px;
    padding: 20px;
    text-align: center;
    border: 1px solid #eee;
}
.kpi h2 {
    font-size: 24px;
}
.kpi p {
    color: var(--gray);
}

/* SUCCESS */
.success-box {
    background: #ecfdf5;
    border: 1px solid #10b981;
    border-radius: 14px;
    padding: 40px;
    text-align: center;
    margin-top: 30px;
}
.success-box h1 {
    font-size: 32px;
    color: #065f46;
}

/* FOOTER */
.footer {
    margin-top: 60px;
    text-align: center;
}
.signature {
    font-family: 'Cairo', sans-serif;
    font-weight: 800;
    font-size: 18px;
    color: var(--green);
}
.copy {
    color: var(--gray);
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
if logo:
    st.markdown(f"""
    <div class="header">
        <div class="header-title">Hawelha Telecom</div>
        <img src="data:image/png;base64,{logo}">
    </div>
    """, unsafe_allow_html=True)

# ================= HELPERS =================
def normalize(t):
    return (t or "").replace("−","-").replace("–","-")

def extract_numbers(text):
    text = normalize(text)
    text = re.sub(r'01[0125]\d{8}', '', text)  # حذف رقم الموبايل
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
                            "محمول": str(phone),
                            "رسوم شهرية": g(0),
                            "رسوم الخدمات": g(1),
                            "إجمالي": g(12)
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
st.markdown("""
<div class="main-card">
    <h2>رفع ملف الفاتورة</h2>
    <p>ارفع ملف PDF وسيتم تحويله إلى Excel</p>
</div>
""", unsafe_allow_html=True)

file = st.file_uploader("", type=["pdf"])

if file:
    if st.button("🚀 بدء التحويل"):

        if mode == "Auto 🤖":
            with pdfplumber.open(file) as pdf:
                text = pdf.pages[0].extract_text() or ""
            lang = "ar" if re.search(r'[\u0600-\u06FF]', text) else "en"
        else:
            lang = "ar" if mode == "عربي 🇪🇬" else "en"

        data = parse_ar(file) if lang == "ar" else parse_en(file)

        if data:
            df = pd.DataFrame(data)

            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="kpi"><h2>{len(df)}</h2><p>عدد الخطوط</p></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="kpi"><h2>{df["رسوم شهرية"].sum():.0f}</h2><p>الرسوم الشهرية</p></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="kpi"><h2>{df["إجمالي"].sum():.0f}</h2><p>الإجمالي</p></div>', unsafe_allow_html=True)

            st.dataframe(df.head(10), use_container_width=True)

            output = io.BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            st.markdown("""
            <div class="success-box">
                <h1>✔ تم التحويل بنجاح</h1>
            </div>
            """, unsafe_allow_html=True)

            st.download_button("📥 تحميل Excel", output, "hawelha.xlsx")

# ================= FOOTER =================
st.markdown("""
<div class="footer">
    <div class="signature">Hawelha Telecom — Built by Najat El Bakry</div>
    <div class="copy">© 2026 All Rights Reserved</div>
</div>
""", unsafe_allow_html=True)
