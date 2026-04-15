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

html, body { font-family: 'Cairo', sans-serif; background: #f8fafc; }

.header {
    background: linear-gradient(135deg, #059669, #10b981);
    padding: 40px;
    border-radius: 18px;
    text-align: center;
    color: white;
    margin-bottom: 25px;
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
    padding: 12px;
    border-radius: 10px;
    width: 100%;
}

.kpi {
    background: white;
    border-radius: 14px;
    padding: 18px;
    text-align: center;
    border-top: 4px solid #10b981;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
if logo:
    st.markdown(f"""
    <div class="header">
        <img src="data:image/png;base64,{logo}" width="300">
        <h1>Hawelha Telecom</h1>
    </div>
    """, unsafe_allow_html=True)

# ================= HELPERS =================
def normalize(text):
    return (text or "").replace("−","-").replace("–","-")

# 🔥 الحل النهائي للسالب
def extract_numbers(text):
    text = normalize(text)

    matches = re.findall(r'(-?\s*\d+(?:\.\d+)?\s*-?)', text)

    numbers = []
    for m in matches:
        m = m.replace(" ", "")
        if m.endswith("-"):
            val = -float(m[:-1])
        else:
            val = float(m)
        numbers.append(val)

    return numbers

# ================= PARSER =================
def parse_ar(file):
    records = []

    with pdfplumber.open(file) as pdf:
        total_pages = len(pdf.pages)

        progress = st.progress(0)

        for p, page in enumerate(pdf.pages[2:], start=2):

            progress.progress(int((p / total_pages) * 100))

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
    <h2>📁 Upload PDF Invoice</h2>
</div>
""", unsafe_allow_html=True)

file = st.file_uploader("", type=["pdf"])

# ================= MAIN =================
if file:

    if st.button("🚀 Start Processing"):

        with st.spinner("Processing..."):

            data = parse_ar(file)

            if data:

                df = pd.DataFrame(data)

                # ================= KPIS =================
                total_lines = len(df)
                total_monthly = df["رسوم شهرية"].sum()
                total_settlement = df["رسوم تسويات"].sum()
                total_total = df["إجمالي"].sum()

                st.markdown("## 📊 Dashboard")

                c1, c2, c3, c4 = st.columns(4)

                c1.markdown(f'<div class="kpi"><h2>{total_lines}</h2><p>عدد الخطوط</p></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="kpi"><h2>{total_monthly:.2f}</h2><p>الرسوم الشهرية</p></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="kpi"><h2>{total_settlement:.2f}</h2><p>التسويات</p></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="kpi"><h2>{total_total:.2f}</h2><p>الإجمالي</p></div>', unsafe_allow_html=True)

                st.dataframe(df.head(10), use_container_width=True)

                excel = to_excel(df)

                st.success("✅ تم التحويل بنجاح")

                st.download_button(
                    "📥 تحميل Excel",
                    excel,
                    file_name="hawelha.xlsx"
                )

            else:
                st.error("No data found")
