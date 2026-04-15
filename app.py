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
    padding: 40px 20px;
    border-radius: 18px;
    text-align: center;
    color: white;
    margin-bottom: 25px;
}

.header img {
    width: 420px;
    max-width: 95%;
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
    font-weight: 700;
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
        <img src="data:image/png;base64,{logo}">
        <h1>Hawelha Telecom</h1>
        <p>PDF → Excel Automation System</p>
    </div>
    """, unsafe_allow_html=True)

# ================= HELPERS =================
def normalize(t):
    return (t or "").replace("−","-").replace("–","-")

PHONE_PATTERN = re.compile(r'(01[0125]\d{8})')

# 🔥 FIX نهائي للسالب
def extract_numbers(text):
    text = normalize(text)

    # توحيد كل أشكال السالب
    text = re.sub(r'(\d+)\s*-\b', r'-\1', text)
    text = re.sub(r'(\d+)\s*-\s', r'-\1', text)
    text = re.sub(r'-\s*(\d+)', r'-\1', text)

    numbers = re.findall(r'-?\d+(?:\.\d+)?', text)

    return [float(x) for x in numbers]

# ================= PARSER =================
def parse_file(file):
    records = []

    with pdfplumber.open(file) as pdf:
        total_pages = len(pdf.pages)

        progress = st.progress(0)
        status = st.empty()

        for idx, page in enumerate(pdf.pages[2:]):

            text_page = page.extract_text()
            if not text_page or "01" not in text_page:
                continue

            percent = int((idx / max(total_pages-2, 1)) * 100)
            progress.progress(percent)
            status.text(f"📄 صفحة {idx+3} من {total_pages}")

            tables = page.extract_tables()
            if not tables:
                continue

            for table in tables:
                i = 0
                while i < len(table):
                    row = table[i]
                    if not row:
                        i += 1
                        continue

                    text = normalize(" ".join([str(c) for c in row if c]))
                    phone_match = PHONE_PATTERN.search(text)

                    if phone_match:
                        phone = phone_match.group(1)

                        vals = extract_numbers(text)

                        if i+1 < len(table):
                            next_text = " ".join([str(c) for c in table[i+1] if c])
                            nxt = extract_numbers(next_text)
                            if len(nxt) > len(vals):
                                vals = nxt
                                i += 1

                        vals.reverse()

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

        progress.progress(100)
        status.text("✅ تم الانتهاء")

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
    <p>Drag & Drop your file</p>
</div>
""", unsafe_allow_html=True)

file = st.file_uploader("", type=["pdf"])

# ================= MAIN =================
if file:

    if st.button("🚀 Start Processing"):

        with st.spinner("Processing..."):

            data = parse_file(file)

            if data:

                df = pd.DataFrame(data)

                # ================= KPIS =================
                total_lines = len(df)
                total_monthly = df["رسوم شهرية"].sum()
                total_settlement = df.get("رسوم تسويات", pd.Series([0])).sum()
                total_total = df["إجمالي"].sum()

                st.markdown("## 📊 Dashboard")

                c1, c2, c3, c4 = st.columns(4)

                c1.markdown(f'<div class="kpi"><h2>{total_lines}</h2><p>عدد الخطوط</p></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="kpi"><h2>{total_monthly:.2f}</h2><p>الرسوم الشهرية</p></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="kpi"><h2>{total_settlement:.2f}</h2><p>التسويات</p></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="kpi"><h2>{total_total:.2f}</h2><p>الإجمالي</p></div>', unsafe_allow_html=True)

                st.dataframe(df.head(10), use_container_width=True)

                excel = to_excel(df)

                st.success("🎉 تم التحويل بنجاح")

                st.download_button(
                    "📥 تحميل Excel",
                    excel,
                    file_name="hawelha_telecom.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            else:
                st.error("No data found")
